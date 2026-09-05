import pytest
import requests

from app.extensions import db
from app.models import Listing, ListingAspect, ListingStatus
from app.services.ebay.publish import PublishService, PublishServiceError


class Response:
    def __init__(self, body=None, *, ok=True, status_code=200): self.body, self.ok, self.status_code = body or {"listingId": "fake-listing-id", "listingUrl": "https://www.sandbox.ebay.com/itm/fake-listing-id"}, ok, status_code
    def json(self): return self.body


class Http:
    def __init__(self, response=None): self.response, self.calls = response or Response(), []
    def post(self, *args, **kwargs): self.calls.append((args, kwargs)); return self.response


class FailingHttp:
    def post(self, *args, **kwargs): raise requests.RequestException("dropped")


def staged_listing(sku="PUBLISH-1"):
    listing = Listing(sku=sku, title="Acme Widget", description="Saved factual description.", condition="Used", quantity=2, final_price="12.50", ebay_category_id="123", ebay_category_name="Widgets", status=ListingStatus.EBAY_STAGED, ebay_inventory_status="STAGED", ebay_offer_status="STAGED", ebay_offer_id="fake-offer-id")
    listing.aspects.append(ListingAspect(name="Brand", value="Acme", required=True))
    return listing


def test_publish_offer_uses_sandbox_endpoint_and_persists_listing_metadata(app):
    with app.app_context():
        listing = staged_listing(); db.session.add(listing); db.session.commit()
        http = Http(); assert PublishService(app.config, http=http, token_provider=lambda: "shared-token").publish_offer(listing) is True
        args, kwargs = http.calls[0]
        assert args[0] == "https://api.sandbox.ebay.com/sell/inventory/v1/offer/fake-offer-id/publish"
        assert kwargs["headers"]["Authorization"] == "Bearer shared-token"
        assert listing.status == ListingStatus.PUBLISHED and listing.ebay_publish_status == "PUBLISHED"
        assert listing.ebay_listing_id == "fake-listing-id" and listing.ebay_listing_url.endswith("fake-listing-id") and listing.ebay_published_at


def test_publish_prevents_double_publish_and_preserves_staged_offer_on_failures(app):
    with app.app_context():
        listing = staged_listing(); db.session.add(listing); db.session.commit()
        service = PublishService(app.config, http=Http(), token_provider=lambda: "token")
        service.publish_offer(listing); assert service.publish_offer(listing) is False
        failed = staged_listing("PUBLISH-2"); db.session.add(failed); db.session.commit()
        with pytest.raises(PublishServiceError, match="could not publish"):
            PublishService(app.config, http=Http(Response({}, ok=False, status_code=400)), token_provider=lambda: "token").publish_offer(failed)
        assert failed.status == ListingStatus.EBAY_STAGED and failed.ebay_publish_status == "FAILED" and failed.ebay_offer_id == "fake-offer-id"
        unknown = staged_listing("PUBLISH-3"); db.session.add(unknown); db.session.commit()
        with pytest.raises(PublishServiceError, match="outcome is unknown"):
            PublishService(app.config, http=FailingHttp(), token_provider=lambda: "token").publish_offer(unknown)
        assert unknown.status == ListingStatus.EBAY_STAGED and unknown.ebay_publish_status == "UNKNOWN"


def test_publish_requires_staged_offer_and_explicit_route_confirmation(client, login, app, monkeypatch):
    with app.app_context():
        listing = staged_listing(); db.session.add(listing); db.session.commit(); listing_id = listing.id
        listing.status = ListingStatus.READY
        with pytest.raises(PublishServiceError, match="Stage a valid"):
            PublishService(app.config, http=Http(), token_provider=lambda: "token").publish_offer(listing)
        listing.status = ListingStatus.EBAY_STAGED; db.session.commit()
    assert client.post(f"/listings/{listing_id}/publish").status_code == 302
    login()
    response = client.post(f"/listings/{listing_id}/publish", data={"publish_confirmation": "no"}, follow_redirects=True)
    assert b"Type PUBLISH" in response.data
    class Service:
        def publish_offer(self, listing): listing.ebay_listing_id = "live-1"; listing.ebay_publish_status = "PUBLISHED"; listing.transition_to(ListingStatus.PUBLISHED); db.session.commit(); return True
    monkeypatch.setattr("app.listings.get_publish_service", lambda: Service())
    response = client.post(f"/listings/{listing_id}/publish", data={"publish_confirmation": "PUBLISH"}, follow_redirects=True)
    assert b"Listing published successfully" in response.data and b"Published successfully" in response.data and b"live-1" in response.data
