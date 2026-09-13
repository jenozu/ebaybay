from decimal import Decimal

import pytest

from app.extensions import db
from app.models import Listing, ListingAspect, ListingImage, ListingStatus
from app.services.ebay.inventory import (
    InventoryService,
    InventoryServiceError,
    inventory_payload,
    product_identifier,
)


class Response:
    def __init__(self, ok=True, status_code=204, payload=None, headers=None):
        self.ok, self.status_code, self.payload = ok, status_code, payload
        self.headers = headers or {}

    def json(self):
        if self.payload is None:
            raise ValueError("no json")
        return self.payload


class Http:
    def __init__(self, response=None):
        self.response, self.calls = response or Response(), []

    def put(self, *args, **kwargs):
        self.calls.append((args, kwargs))
        return self.response


class SequenceHttp:
    def __init__(self, responses):
        self.responses, self.calls = list(responses), []

    def put(self, *args, **kwargs):
        self.calls.append((args, kwargs))
        return self.responses.pop(0)


def staged_listing(sku="STAGE-1"):
    listing = Listing(
        sku=sku,
        title="Acme AX-1 Widget",
        description="Known facts only.",
        brand="Acme",
        mpn="AX-1",
        gtin="4006381333931",
        condition="Used",
        quantity=2,
        final_price=Decimal("10.00"),
        status=ListingStatus.READY,
    )
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
    assert payload["product"]["mpn"] == "AX-1"
    assert payload["product"]["ean"] == ["4006381333931"]


def test_product_identifier_classifies_supported_gtins_and_rejects_placeholder_text():
    assert product_identifier("036000291452") == ("upc", "036000291452")
    assert product_identifier("4006 3813 3393 1") == ("ean", "4006381333931")
    assert product_identifier("978-0-306-40615-7") == ("isbn", "9780306406157")
    assert product_identifier("0-306-40615-2") == ("isbn", "0306406152")
    assert product_identifier("") is None
    with pytest.raises(ValueError, match="valid UPC-12"):
        product_identifier("Test GTIN")


def test_inventory_payload_rejects_invalid_gtin_before_calling_ebay():
    listing = staged_listing()
    listing.gtin = "Test GTIN"
    with pytest.raises(InventoryServiceError, match="valid UPC-12"):
        inventory_payload(listing)


def test_inventory_stage_uses_shared_token_canadian_locale_and_is_idempotent(app):
    with app.app_context():
        listing = staged_listing("STAGE/1")
        db.session.add(listing)
        db.session.commit()
        http = Http()
        service = InventoryService(app.config, http=http, token_provider=lambda: "shared-token")
        assert service.stage(listing) is True
        args, kwargs = http.calls[0]
        assert args[0] == "https://api.sandbox.ebay.com/sell/inventory/v1/inventory_item/STAGE%2F1"
        assert kwargs["headers"]["Authorization"] == "Bearer shared-token"
        assert kwargs["headers"]["Content-Language"] == "en-CA"
        assert kwargs["headers"]["Accept-Language"] == "en-CA"
        assert kwargs["json"]["product"]["title"] == "Acme AX-1 Widget"
        assert listing.ebay_inventory_status == "STAGED" and listing.ebay_inventory_staged_at
        assert service.stage(listing) is False and len(http.calls) == 1


def test_inventory_staging_retries_transient_500_and_can_recover(app):
    with app.app_context():
        listing = staged_listing("STAGE-RETRY")
        db.session.add(listing)
        db.session.commit()
        transient = Response(False, 500, {
            "errors": [{
                "errorId": 25001,
                "domain": "API_INVENTORY",
                "category": "REQUEST",
                "message": "A system error has occurred. Core Inventory Service internal error",
            }],
        })
        http = SequenceHttp([transient, transient, Response(True, 204)])
        sleeps = []
        service = InventoryService(
            app.config,
            http=http,
            token_provider=lambda: "token",
            sleeper=sleeps.append,
        )
        assert service.stage(listing) is True
        assert len(http.calls) == 3
        assert sleeps == [1.0, 2.0]
        assert listing.ebay_inventory_status == "STAGED"
        assert listing.ebay_inventory_error is None


def test_inventory_staging_exhausts_transient_retries_with_safe_diagnostic(app, caplog):
    with app.app_context():
        listing = staged_listing("STAGE-500")
        db.session.add(listing)
        db.session.commit()
        transient = Response(False, 500, {
            "errors": [{
                "errorId": 25001,
                "domain": "API_INVENTORY",
                "category": "REQUEST",
                "message": "A system error has occurred. Core Inventory Service internal error",
                "parameters": [{"value": "do-not-log-this"}],
            }],
        }, headers={"Retry-After": "0"})
        http = SequenceHttp([transient, transient, transient])
        sleeps = []
        service = InventoryService(
            app.config,
            http=http,
            token_provider=lambda: "super-secret-token",
            sleeper=sleeps.append,
        )
        with caplog.at_level("WARNING"):
            with pytest.raises(InventoryServiceError, match="temporarily unavailable after 3 attempts"):
                service.stage(listing)
        assert len(http.calls) == 3
        assert sleeps == [0.0, 0.0]
        assert listing.ebay_inventory_status == "FAILED"
        assert "HTTP 500" in listing.ebay_inventory_error
        assert "25001" in listing.ebay_inventory_error
        combined_logs = "\n".join(record.getMessage() for record in caplog.records)
        assert "25001" in combined_logs
        assert "super-secret-token" not in combined_logs
        assert "do-not-log-this" not in combined_logs


def test_inventory_staging_rejects_unapproved_or_unuploaded_images_and_records_safe_errors(app):
    with app.app_context():
        listing = staged_listing()
        listing.status = ListingStatus.DRAFT
        db.session.add(listing)
        db.session.commit()
        with pytest.raises(InventoryServiceError, match="approved READY"):
            InventoryService(app.config, http=Http(), token_provider=lambda: "token").stage(listing)
        listing.status = ListingStatus.READY
        listing.images[0].ebay_image_url = None
        listing.images[1].ebay_image_url = None
        with pytest.raises(InventoryServiceError, match="Upload every"):
            inventory_payload(listing)
        listing = staged_listing("STAGE-2")
        db.session.add(listing)
        db.session.commit()
        with pytest.raises(InventoryServiceError, match="rejected"):
            InventoryService(app.config, http=Http(Response(False, 400)), token_provider=lambda: "token").stage(listing)
        assert listing.ebay_inventory_status == "FAILED" and "token" not in (listing.ebay_inventory_error or "")


def test_inventory_rejection_logs_and_persists_only_safe_ebay_fields(app, caplog):
    with app.app_context():
        listing = staged_listing("STAGE-DIAGNOSTIC")
        db.session.add(listing)
        db.session.commit()
        response = Response(False, 400, {
            "errors": [{
                "errorId": 25002,
                "domain": "API_INVENTORY",
                "category": "REQUEST",
                "message": "A required field is missing.",
                "parameters": [{"name": "secret", "value": "do-not-log-this"}],
            }],
            "access_token": "also-do-not-log-this",
        })
        service = InventoryService(app.config, http=Http(response), token_provider=lambda: "super-secret-token")
        with caplog.at_level("WARNING"):
            with pytest.raises(InventoryServiceError, match="25002"):
                service.stage(listing)
        assert listing.ebay_inventory_status == "FAILED"
        assert "HTTP 400" in listing.ebay_inventory_error
        assert "25002" in listing.ebay_inventory_error
        assert "A required field is missing." in listing.ebay_inventory_error
        combined_logs = "\n".join(record.getMessage() for record in caplog.records)
        assert '"status": 400' in combined_logs
        assert '"errorId": "25002"' in combined_logs
        assert '"domain": "API_INVENTORY"' in combined_logs
        assert '"category": "REQUEST"' in combined_logs
        assert "super-secret-token" not in combined_logs
        assert "do-not-log-this" not in combined_logs
        assert "also-do-not-log-this" not in combined_logs
        assert "do-not-log-this" not in listing.ebay_inventory_error


def test_inventory_staging_route_is_protected_and_never_changes_to_live(client, login, app, monkeypatch):
    with app.app_context():
        listing = staged_listing()
        db.session.add(listing)
        db.session.commit()
        listing_id = listing.id
    assert client.post(f"/listings/{listing_id}/inventory/stage").status_code == 302
    login()

    class Service:
        def stage(self, listing):
            listing.ebay_inventory_status = "STAGED"
            db.session.commit()
            return True

    monkeypatch.setattr("app.listings.get_inventory_service", lambda: Service())
    response = client.post(f"/listings/{listing_id}/inventory/stage", follow_redirects=True)
    assert b"staged (not live)" in response.data and b"Stage eBay Inventory Item" in response.data
    with app.app_context():
        assert db.session.get(Listing, listing_id).status == ListingStatus.READY
