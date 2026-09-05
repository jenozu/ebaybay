from decimal import Decimal

import pytest
import requests

from app.extensions import db
from app.models import EbayConnection, Listing, ListingStatus
from app.services.ebay.offers import OfferService, OfferServiceError, offer_payload


class Response:
    def __init__(self, body=None, *, ok=True, status_code=201): self.body, self.ok, self.status_code = body or {"offerId": "fake-offer-id"}, ok, status_code
    def json(self): return self.body


class Http:
    def __init__(self, response=None): self.response, self.calls = response or Response(), []
    def post(self, *args, **kwargs): self.calls.append((args, kwargs)); return self.response


class FailingHttp:
    def post(self, *args, **kwargs): raise requests.RequestException("connection dropped")


def ready_defaults():
    connection = EbayConnection(environment="sandbox", marketplace_id="EBAY_CA", status="CONNECTED")
    connection.default_payment_policy_id = "payment-1"; connection.default_fulfillment_policy_id = "fulfillment-1"; connection.default_return_policy_id = "return-1"; connection.default_merchant_location_key = "warehouse-1"
    return connection


def offer_listing(sku="OFFER-1"):
    return Listing(sku=sku, title="Acme Widget", description="Saved factual description.", condition="Used", quantity=2, final_price=Decimal("12.50"), ebay_category_id="123", status=ListingStatus.READY, ebay_inventory_status="STAGED")


def test_offer_payload_uses_saved_defaults_and_fixed_price_contract(app):
    with app.app_context():
        db.session.add(ready_defaults()); db.session.commit()
        payload = offer_payload(offer_listing(), app.config)
        assert payload == {
            "sku": "OFFER-1", "marketplaceId": "EBAY_CA", "format": "FIXED_PRICE", "availableQuantity": 2,
            "categoryId": "123", "listingDescription": "Saved factual description.", "listingDuration": "GTC", "merchantLocationKey": "warehouse-1",
            "pricingSummary": {"price": {"value": "12.50", "currency": "CAD"}},
            "listingPolicies": {"paymentPolicyId": "payment-1", "fulfillmentPolicyId": "fulfillment-1", "returnPolicyId": "return-1"},
        }


def test_create_offer_uses_sandbox_endpoint_persists_offer_and_sets_ebay_staged(app):
    with app.app_context():
        db.session.add_all([ready_defaults(), offer_listing()]); db.session.commit()
        listing = Listing.query.filter_by(sku="OFFER-1").one(); http = Http()
        assert OfferService(app.config, http=http, token_provider=lambda: "shared-token").stage(listing) is True
        args, kwargs = http.calls[0]
        assert args[0] == "https://api.sandbox.ebay.com/sell/inventory/v1/offer"
        assert kwargs["headers"]["Authorization"] == "Bearer shared-token"
        assert kwargs["json"]["marketplaceId"] == "EBAY_CA" and kwargs["json"]["sku"] == "OFFER-1"
        assert listing.ebay_offer_id == "fake-offer-id" and listing.ebay_offer_status == "STAGED"
        assert listing.status == ListingStatus.EBAY_STAGED


def test_offer_staging_is_idempotent_and_blocks_conflicting_or_ambiguous_retries(app):
    with app.app_context():
        db.session.add_all([ready_defaults(), offer_listing()]); db.session.commit(); listing = Listing.query.filter_by(sku="OFFER-1").one()
        http = Http(); service = OfferService(app.config, http=http, token_provider=lambda: "token")
        service.stage(listing); assert service.stage(listing) is False and len(http.calls) == 1
        listing.final_price = Decimal("13.00")
        with pytest.raises(OfferServiceError, match="duplicate"):
            service.stage(listing)
        other = offer_listing("OFFER-2"); db.session.add(other); db.session.commit()
        with pytest.raises(OfferServiceError, match="outcome is unknown"):
            OfferService(app.config, http=FailingHttp(), token_provider=lambda: "token").stage(other)
        assert other.ebay_offer_status == "UNKNOWN"


def test_offer_preconditions_errors_and_route_is_protected(client, login, app, monkeypatch):
    with app.app_context():
        listing = offer_listing(); listing.ebay_inventory_status = "NOT_STAGED"; db.session.add(listing); db.session.commit(); listing_id = listing.id
        with pytest.raises(OfferServiceError, match="Inventory Item"):
            offer_payload(listing, app.config)
    assert client.post(f"/listings/{listing_id}/offer/stage").status_code == 302
    login()
    class Service:
        def stage(self, listing): listing.ebay_offer_status = "STAGED"; listing.ebay_offer_id = "fake"; listing.transition_to(ListingStatus.EBAY_STAGED); db.session.commit(); return True
    with app.app_context():
        listing = db.session.get(Listing, listing_id); listing.ebay_inventory_status = "STAGED"; db.session.commit()
    monkeypatch.setattr("app.listings.get_offer_service", lambda: Service())
    response = client.post(f"/listings/{listing_id}/offer/stage", follow_redirects=True)
    assert b"Unpublished eBay offer staged" in response.data and b"Offer ID fake" in response.data
