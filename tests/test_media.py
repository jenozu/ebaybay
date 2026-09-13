from pathlib import Path

import pytest

from app.extensions import db
from app.models import Listing, ListingImage, ListingStatus
from app.services.ebay.media import MediaService, MediaServiceError
from app.services.ebay.oauth import OAuthService


class Response:
    def __init__(self, body=None, *, status_code=200, ok=None, headers=None, json_error=False):
        self.body = body
        self.status_code = status_code
        self.ok = 200 <= status_code < 300 if ok is None else ok
        self.headers = headers or {}
        self.json_error = json_error

    def json(self):
        if self.json_error:
            raise ValueError("malformed json")
        return self.body


class Http:
    def __init__(self, *, posts=(), gets=()):
        self.posts = list(posts)
        self.gets = list(gets)
        self.calls = []

    def post(self, *args, **kwargs):
        self.calls.append(("POST", args, kwargs))
        return self.posts.pop(0)

    def get(self, *args, **kwargs):
        self.calls.append(("GET", args, kwargs))
        return self.gets.pop(0)


def created(image_id):
    return Response(
        status_code=201,
        headers={"Location": f"https://apim.ebay.com/commerce/media/v1_beta/image/{image_id}"},
    )


def details(image_id):
    return Response({"imageUrl": f"https://i.ebayimg.com/{image_id}.jpg"})


def image(app, name="photo.jpg", data=b"image-bytes", order=0):
    path = app.config["UPLOAD_DIR"] / name
    path.write_bytes(data)
    return ListingImage(
        filename=name,
        original_filename=name,
        mime_type="image/jpeg",
        size_bytes=len(data),
        sort_order=order,
    )


def persisted_listing(app, item, sku="MEDIA-SERVICE"):
    listing = Listing(sku=sku, status=ListingStatus.READY, quantity=1)
    listing.images.append(item)
    db.session.add(listing)
    db.session.commit()
    return listing


def test_media_upload_uses_multipart_201_location_get_image_and_persists_resource(app):
    with app.app_context():
        item = image(app)
        persisted_listing(app, item)
        OAuthService(app.config).save_token_response(
            {"access_token": "shared-token", "refresh_token": "refresh", "expires_in": 7200},
            require_refresh=True,
        )
        http = Http(posts=[created("fake-image-id")], gets=[details("fake-image-id")])

        assert MediaService(app.config, http=http, sleeper=lambda _: None).upload_image(
            item, app.config["UPLOAD_DIR"] / item.filename
        ) is True

        method, args, kwargs = http.calls[0]
        assert method == "POST"
        assert args[0] == "https://api.sandbox.ebay.com/commerce/media/v1_beta/image/create_image_from_file"
        assert kwargs["headers"]["Authorization"] == "Bearer shared-token"
        assert kwargs["headers"]["Accept"] == "application/json"
        assert "Content-Type" not in kwargs["headers"]
        assert "data" not in kwargs
        assert kwargs["files"] == {"image": ("photo.jpg", b"image-bytes", "image/jpeg")}

        method, args, kwargs = http.calls[1]
        assert method == "GET"
        assert args[0] == "https://api.sandbox.ebay.com/commerce/media/v1_beta/image/fake-image-id"
        assert kwargs["headers"]["Authorization"] == "Bearer shared-token"
        assert item.ebay_image_id == "fake-image-id"
        assert item.ebay_image_url == "https://i.ebayimg.com/fake-image-id.jpg"
        assert item.ebay_upload_status == "UPLOADED"
        assert item.ebay_upload_fingerprint
        db.session.expire_all()
        stored = db.session.get(ListingImage, item.id)
        assert stored.ebay_image_id == "fake-image-id"
        assert stored.ebay_image_url == "https://i.ebayimg.com/fake-image-id.jpg"


def test_media_service_uses_current_commerce_media_paths_in_production(app):
    config = dict(app.config)
    config["EBAY_ENVIRONMENT"] = "production"
    config.pop("EBAY_API_BASE", None)
    service = MediaService(config, token_provider=lambda: "token")
    assert service.endpoint == "https://api.ebay.com/commerce/media/v1_beta/image/create_image_from_file"
    assert service.image_endpoint("image id") == "https://api.ebay.com/commerce/media/v1_beta/image/image%20id"


@pytest.mark.parametrize(
    "response",
    [
        Response(status_code=201),
        Response(status_code=201, headers={"Location": "https://apim.ebay.com/not-an-image/id"}),
        Response(status_code=200, headers={"Location": "https://apim.ebay.com/commerce/media/v1_beta/image/id"}),
    ],
)
def test_media_upload_rejects_missing_malformed_or_non_201_create_response(app, response):
    with app.app_context():
        item = image(app)
        persisted_listing(app, item)
        http = Http(posts=[response])
        with pytest.raises(MediaServiceError, match="invalid image-upload response"):
            MediaService(app.config, http=http, token_provider=lambda: "token", sleeper=lambda _: None).upload_image(
                item, app.config["UPLOAD_DIR"] / item.filename
            )
        assert [call[0] for call in http.calls] == ["POST"]
        assert item.ebay_upload_status == "FAILED"
        assert item.ebay_image_url is None


def test_media_upload_rejects_malformed_get_image_and_reuses_created_id_on_retry(app):
    with app.app_context():
        item = image(app)
        persisted_listing(app, item)
        first_http = Http(posts=[created("recover-me")], gets=[Response({"expirationDate": "2099-01-01"})])
        service = MediaService(app.config, http=first_http, token_provider=lambda: "token", sleeper=lambda _: None)

        with pytest.raises(MediaServiceError, match="invalid image-details response"):
            service.upload_image(item, app.config["UPLOAD_DIR"] / item.filename)
        assert item.ebay_image_id == "recover-me"
        assert item.ebay_image_url is None
        assert item.ebay_upload_fingerprint
        assert item.ebay_upload_status == "FAILED"

        recovery_http = Http(gets=[details("recover-me")])
        recovered = MediaService(
            app.config, http=recovery_http, token_provider=lambda: "token", sleeper=lambda _: None
        ).upload_image(item, app.config["UPLOAD_DIR"] / item.filename)
        assert recovered is True
        assert [call[0] for call in recovery_http.calls] == ["GET"]
        assert item.ebay_image_url == "https://i.ebayimg.com/recover-me.jpg"
        assert item.ebay_upload_status == "UPLOADED"


def test_media_upload_retries_transient_create_and_get_image_failures(app):
    with app.app_context():
        item = image(app)
        persisted_listing(app, item)
        waits = []
        http = Http(
            posts=[Response({"error": "busy"}, status_code=503), created("image-2")],
            gets=[Response({"error": "busy"}, status_code=503), details("image-2")],
        )
        MediaService(
            app.config, http=http, token_provider=lambda: "token", sleeper=waits.append
        ).upload_image(item, app.config["UPLOAD_DIR"] / item.filename)
        assert [call[0] for call in http.calls] == ["POST", "POST", "GET", "GET"]
        assert waits == [0.1, 0.1]
        assert item.ebay_image_id == "image-2"
        assert item.ebay_upload_status == "UPLOADED"


def test_media_upload_does_not_retry_permanent_create_rejection(app):
    with app.app_context():
        item = image(app, "bad.jpg")
        persisted_listing(app, item, "MEDIA-FAIL")
        http = Http(posts=[Response({"error": "bad"}, status_code=400)])
        with pytest.raises(MediaServiceError, match="rejected"):
            MediaService(app.config, http=http, token_provider=lambda: "token", sleeper=lambda _: None).upload_image(
                item, app.config["UPLOAD_DIR"] / item.filename
            )
        assert len(http.calls) == 1
        assert item.ebay_upload_status == "FAILED"


def test_media_upload_is_locally_idempotent_and_preserves_listing_image_order(app):
    with app.app_context():
        later = image(app, "second.jpg", b"second", 1)
        earlier = image(app, "first.jpg", b"first", 0)
        listing = Listing(sku="MEDIA-1", status=ListingStatus.READY, quantity=1)
        listing.images.extend([later, earlier])
        db.session.add(listing)
        db.session.commit()
        http = Http(
            posts=[created("one"), created("two")],
            gets=[details("one"), details("two")],
        )
        service = MediaService(app.config, http=http, token_provider=lambda: "token", sleeper=lambda _: None)

        assert service.upload_listing_images(listing, app.config["UPLOAD_DIR"]) == (2, 0)
        upload_calls = [call for call in http.calls if call[0] == "POST"]
        assert [call[2]["files"]["image"][1] for call in upload_calls] == [b"first", b"second"]
        assert service.upload_listing_images(listing, app.config["UPLOAD_DIR"]) == (0, 2)
        assert len(http.calls) == 4


def test_media_upload_requires_approved_listing_and_route_is_protected(client, login, app, monkeypatch):
    with app.app_context():
        listing = Listing(sku="MEDIA-ROUTE", status=ListingStatus.DRAFT, quantity=1)
        listing.images.append(image(app, "route.jpg"))
        db.session.add(listing)
        db.session.commit()
        listing_id = listing.id
    assert client.post(f"/listings/{listing_id}/images/upload").status_code == 302
    login()
    response = client.post(f"/listings/{listing_id}/images/upload", follow_redirects=True)
    assert b"Only an approved READY listing" in response.data
    with app.app_context():
        db.session.get(Listing, listing_id).status = ListingStatus.READY
        db.session.commit()

    class Service:
        def upload_listing_images(self, listing, upload_dir):
            return (1, 0)

    monkeypatch.setattr("app.listings.get_media_service", lambda: Service())
    response = client.post(f"/listings/{listing_id}/images/upload", follow_redirects=True)
    assert b"1 uploaded" in response.data
    assert b"Upload Approved Images to eBay" in response.data and b"EBAY MEDIA" in response.data and b"PENDING" in response.data
