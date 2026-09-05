from decimal import Decimal

import pytest

from app.extensions import db
from app.models import Listing, ListingAspect, ListingImage, ListingStatus
from app.services.ebay.inventory import InventoryService, InventoryServiceError, inventory_payload


class Response:
    def __init__(self, ok=True, status_code=204): self.ok, self.status_code = ok, status_code


class Http:
    def __init__(self, response=None): self.response, self.calls = response or Response(), []
    def put(self, *args, **kwargs): self.calls.append((args, kwargs)); return self.response


def staged_listing(sku="STAGE-1"):
    listing = Listing(sku=sku, title="Acme AX-1 Widget", description="Known facts only.", brand="Acme", mpn="AX-1", gtin="1234567890123", condition="Used", quantity=2, final_price=Decimal("10.00"), status=ListingStatus.READY)
    listing.images.append(ListingImage(filename="x.jpg", original_filename="x.jpg", mime_type="image/jpeg", size_bytes=1, sort_order=1, ebay_image_url="https://i.ebayimg.com/second.jpg"))
    listing.images.append(ListingImage(filename="y.jpg", original_filename="y.jpg", mime_type="image/jpeg", size_bytes=1, sort_order=0, ebay_image_url="https://i.ebayimg.com/first.jpg"))
    listing.aspects.append(ListingAspect(name="Brand", value="Acme", required=True))
    return listing


def test_inventory_payload_is_factual_and_preserves_hosted_image_order():
    payload = inventory_payload(staged_listing())
    assert payload["condition"] == "USED_EXCELLENT"
    assert payload["availability"]["shipToLocationAvailability"]["quantity"] == 2
    assert payload["product"]["imageUrls"] == ["https://i.ebayimg.com/first.jpg", "https://i.ebayimg.com/second.jpg"]
    assert payload["product"]["aspects"] == {"Brand": ["Acme"]}
    assert payload["product"]["mpn"] == "AX-1" and payload["product"]["ean"] == ["1234567890123"]


def test_inventory_stage_uses_shared_token_persists_status_and_is_idempotent(app):
    with app.app_context():
        listing = staged_listing(); db.session.add(listing); db.session.commit()
        http = Http(); service = InventoryService(app.config, http=http, token_provider=lambda: "shared-token")
        assert service.stage(listing) is True
        args, kwargs = http.calls[0]
        assert args[0] == "https://api.sandbox.ebay.com/sell/inventory/v1/inventory_item/STAGE-1"
        assert kwargs["headers"]["Authorization"] == "Bearer shared-token"
        assert kwargs["json"]["product"]["title"] == "Acme AX-1 Widget"
        assert listing.ebay_inventory_status == "STAGED" and listing.ebay_inventory_staged_at
        assert service.stage(listing) is False and len(http.calls) == 1


def test_inventory_staging_rejects_unapproved_or_unuploaded_images_and_records_safe_errors(app):
    with app.app_context():
        listing = staged_listing(); listing.status = ListingStatus.DRAFT; db.session.add(listing); db.session.commit()
        with pytest.raises(InventoryServiceError, match="approved READY"):
            InventoryService(app.config, http=Http(), token_provider=lambda: "token").stage(listing)
        listing.status = ListingStatus.READY; listing.images[0].ebay_image_url = None; listing.images[1].ebay_image_url = None
        with pytest.raises(InventoryServiceError, match="Upload every"):
            inventory_payload(listing)
        listing = staged_listing("STAGE-2"); db.session.add(listing); db.session.commit()
        with pytest.raises(InventoryServiceError, match="rejected"):
            InventoryService(app.config, http=Http(Response(False, 400)), token_provider=lambda: "token").stage(listing)
        assert listing.ebay_inventory_status == "FAILED" and "token" not in (listing.ebay_inventory_error or "")


def test_inventory_staging_route_is_protected_and_never_changes_to_live(client, login, app, monkeypatch):
    with app.app_context():
        listing = staged_listing(); db.session.add(listing); db.session.commit(); listing_id = listing.id
    assert client.post(f"/listings/{listing_id}/inventory/stage").status_code == 302
    login()
    class Service:
        def stage(self, listing): listing.ebay_inventory_status = "STAGED"; db.session.commit(); return True
    monkeypatch.setattr("app.listings.get_inventory_service", lambda: Service())
    response = client.post(f"/listings/{listing_id}/inventory/stage", follow_redirects=True)
    assert b"staged (not live)" in response.data and b"Stage eBay Inventory Item" in response.data
    with app.app_context(): assert db.session.get(Listing, listing_id).status == ListingStatus.READY
