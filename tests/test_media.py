from pathlib import Path

import pytest

from app.extensions import db
from app.models import Listing, ListingImage, ListingStatus
from app.services.ebay.media import MediaService, MediaServiceError
from app.services.ebay.oauth import OAuthService


class Response:
    def __init__(self, body, *, ok=True, status_code=201): self.body, self.ok, self.status_code = body, ok, status_code
    def json(self): return self.body


class Http:
    def __init__(self, responses): self.responses, self.calls = list(responses), []
    def post(self, *args, **kwargs): self.calls.append((args, kwargs)); return self.responses.pop(0)


def image(app, name="photo.jpg", data=b"image-bytes", order=0):
    path = app.config["UPLOAD_DIR"] / name; path.write_bytes(data)
    return ListingImage(filename=name, original_filename=name, mime_type="image/jpeg", size_bytes=len(data), sort_order=order)


def persisted_listing(app, item, sku="MEDIA-SERVICE"):
    listing = Listing(sku=sku, status=ListingStatus.READY, quantity=1)
    listing.images.append(item)
    db.session.add(listing); db.session.commit()
    return listing


def test_media_upload_uses_sandbox_endpoint_shared_token_and_persists_resource(app):
    with app.app_context():
        item = image(app); persisted_listing(app, item)
        OAuthService(app.config).save_token_response({"access_token": "shared-token", "refresh_token": "refresh", "expires_in": 7200}, require_refresh=True)
        http = Http([Response({"imageId": "fake-image-id", "imageUrl": "https://i.ebayimg.com/fake.jpg"})])
        assert MediaService(app.config, http=http, sleeper=lambda _: None).upload_image(item, app.config["UPLOAD_DIR"] / item.filename) is True
        args, kwargs = http.calls[0]
        assert args[0] == "https://api.sandbox.ebay.com/sell/media/v1/image/create_image_from_file"
        assert kwargs["headers"]["Authorization"] == "Bearer shared-token"
        assert kwargs["headers"]["Content-Type"] == "image/jpeg"
        assert item.ebay_image_id == "fake-image-id" and item.ebay_image_url == "https://i.ebayimg.com/fake.jpg"
        assert item.ebay_upload_status == "UPLOADED"


def test_media_upload_retries_only_transient_errors_and_has_bounded_failure(app):
    with app.app_context():
        item = image(app); persisted_listing(app, item)
        waits, http = [], Http([Response({"error": "busy"}, ok=False, status_code=503), Response({"imageId": "image-2", "imageUrl": "https://i.ebayimg.com/2.jpg"})])
        MediaService(app.config, http=http, token_provider=lambda: "token", sleeper=waits.append).upload_image(item, app.config["UPLOAD_DIR"] / item.filename)
        assert len(http.calls) == 2 and waits == [0.1]
        item2 = image(app, "bad.jpg"); persisted_listing(app, item2, "MEDIA-FAIL")
        http = Http([Response({"error": "bad"}, ok=False, status_code=400)])
        with pytest.raises(MediaServiceError): MediaService(app.config, http=http, token_provider=lambda: "token", sleeper=lambda _: None).upload_image(item2, app.config["UPLOAD_DIR"] / item2.filename)
        assert len(http.calls) == 1 and item2.ebay_upload_status == "FAILED"


def test_media_upload_is_locally_idempotent_and_preserves_listing_image_order(app):
    with app.app_context():
        first, second = image(app, "second.jpg", b"second", 1), image(app, "first.jpg", b"first", 0)
        listing = Listing(sku="MEDIA-1", status=ListingStatus.READY, quantity=1); listing.images.extend([first, second]); db.session.add(listing); db.session.commit()
        http = Http([Response({"imageId": "one", "imageUrl": "https://i.ebayimg.com/one.jpg"}), Response({"imageId": "two", "imageUrl": "https://i.ebayimg.com/two.jpg"})])
        service = MediaService(app.config, http=http, token_provider=lambda: "token", sleeper=lambda _: None)
        assert service.upload_listing_images(listing, app.config["UPLOAD_DIR"]) == (2, 0)
        assert [call[1]["data"] for call in http.calls] == [b"first", b"second"]
        assert service.upload_listing_images(listing, app.config["UPLOAD_DIR"]) == (0, 2)
        assert len(http.calls) == 2


def test_media_upload_requires_approved_listing_and_route_is_protected(client, login, app, monkeypatch):
    with app.app_context():
        listing = Listing(sku="MEDIA-ROUTE", status=ListingStatus.DRAFT, quantity=1); listing.images.append(image(app, "route.jpg")); db.session.add(listing); db.session.commit(); listing_id = listing.id
    assert client.post(f"/listings/{listing_id}/images/upload").status_code == 302
    login()
    response = client.post(f"/listings/{listing_id}/images/upload", follow_redirects=True)
    assert b"Only an approved READY listing" in response.data
    with app.app_context(): db.session.get(Listing, listing_id).status = ListingStatus.READY; db.session.commit()
    class Service:
        def upload_listing_images(self, listing, upload_dir): return (1, 0)
    monkeypatch.setattr("app.listings.get_media_service", lambda: Service())
    response = client.post(f"/listings/{listing_id}/images/upload", follow_redirects=True)
    assert b"1 uploaded" in response.data
    assert b"Upload Approved Images to eBay" in response.data and b"EBAY MEDIA" in response.data and b"PENDING" in response.data
