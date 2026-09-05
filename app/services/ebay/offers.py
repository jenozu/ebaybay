"""Creation of unpublished fixed-price eBay offers for staged Inventory Items."""
from __future__ import annotations

import hashlib
import json
from decimal import Decimal, InvalidOperation

import requests

from ...extensions import db
from ...models import Listing, ListingStatus, utcnow
from .account import saved_defaults
from .oauth import OAuthError, get_oauth_service


class OfferServiceError(OAuthError):
    """Safe Offer API error that never includes eBay response or token data."""


def offer_payload(listing: Listing, config: dict) -> dict:
    """Map only saved, approved facts into the unpublished Offer payload."""
    if listing.ebay_inventory_status != "STAGED":
        raise OfferServiceError("Stage the eBay Inventory Item successfully before creating an offer.")
    if not listing.ebay_category_id:
        raise OfferServiceError("Select an eBay category before creating an offer.")
    if not listing.description:
        raise OfferServiceError("Add a listing description before creating an offer.")
    try:
        price = Decimal(str(listing.final_price))
        if price <= 0:
            raise InvalidOperation
    except (InvalidOperation, TypeError):
        raise OfferServiceError("Set a final price greater than zero before creating an offer.")
    defaults = saved_defaults(config)
    if not all((defaults.payment_policy_id, defaults.fulfillment_policy_id, defaults.return_policy_id, defaults.merchant_location_key)):
        raise OfferServiceError("Select all seller policy and inventory-location defaults in eBay Settings before creating an offer.")
    listing_format = config.get("EBAY_LISTING_FORMAT", "FIXED_PRICE")
    if listing_format != "FIXED_PRICE":
        raise OfferServiceError("Phase 12 supports FIXED_PRICE offers only.")
    return {
        "sku": listing.sku,
        "marketplaceId": config["EBAY_MARKETPLACE_ID"],
        "format": "FIXED_PRICE",
        "availableQuantity": listing.quantity,
        "categoryId": listing.ebay_category_id,
        "listingDescription": listing.description,
        "listingDuration": config.get("EBAY_LISTING_DURATION", "GTC"),
        "merchantLocationKey": defaults.merchant_location_key,
        "pricingSummary": {"price": {"value": f"{price:.2f}", "currency": config["EBAY_CURRENCY"]}},
        "listingPolicies": {"paymentPolicyId": defaults.payment_policy_id, "fulfillmentPolicyId": defaults.fulfillment_policy_id, "returnPolicyId": defaults.return_policy_id},
    }


class OfferService:
    def __init__(self, config: dict, *, http=None, token_provider=None):
        self.config = config
        self.http = http or requests
        self.token_provider = token_provider or (lambda: get_oauth_service(config).get_access_token())

    @property
    def base_url(self) -> str:
        configured = self.config.get("EBAY_API_BASE")
        if configured:
            return configured.rstrip("/")
        return "https://api.sandbox.ebay.com" if self.config["EBAY_ENVIRONMENT"].lower() == "sandbox" else "https://api.ebay.com"

    def stage(self, listing: Listing) -> bool:
        if listing.status not in {ListingStatus.READY, ListingStatus.EBAY_STAGED}:
            raise OfferServiceError("Only an approved READY listing can create an unpublished eBay offer.")
        if listing.ebay_offer_status == "UNKNOWN":
            raise OfferServiceError("Offer creation outcome is unknown. Do not retry automatically; verify the eBay seller account first.")
        payload = offer_payload(listing, self.config)
        fingerprint = hashlib.sha256(json.dumps(payload, sort_keys=True, separators=(",", ":")).encode()).hexdigest()
        if listing.ebay_offer_id:
            if listing.ebay_offer_payload_fingerprint == fingerprint:
                return False
            raise OfferServiceError("This listing already has an unpublished eBay offer with different saved details. Do not create a duplicate offer.")
        listing.ebay_offer_status, listing.ebay_offer_error = "STAGING", None
        db.session.commit()
        try:
            response = self.http.post(f"{self.base_url}/sell/inventory/v1/offer", json=payload, headers={"Authorization": f"Bearer {self.token_provider()}", "Content-Type": "application/json", "Accept": "application/json"}, timeout=self.config["EBAY_HTTP_TIMEOUT_SECONDS"])
        except requests.RequestException as exc:
            listing.ebay_offer_status, listing.ebay_offer_error = "UNKNOWN", "eBay offer creation outcome is unknown. Verify eBay before retrying."
            db.session.commit()
            raise OfferServiceError(listing.ebay_offer_error) from exc
        if not getattr(response, "ok", False):
            listing.ebay_offer_status, listing.ebay_offer_error = "FAILED", "eBay rejected the unpublished offer. Review the listing and seller defaults, then try again."
            db.session.commit()
            raise OfferServiceError(listing.ebay_offer_error)
        try:
            response_payload = response.json()
        except (ValueError, TypeError) as exc:
            listing.ebay_offer_status, listing.ebay_offer_error = "UNKNOWN", "eBay offer creation outcome is unknown. Verify eBay before retrying."
            db.session.commit()
            raise OfferServiceError(listing.ebay_offer_error) from exc
        offer_id = response_payload.get("offerId") if isinstance(response_payload, dict) else None
        if not isinstance(offer_id, str) or not offer_id:
            listing.ebay_offer_status, listing.ebay_offer_error = "UNKNOWN", "eBay offer creation outcome is unknown. Verify eBay before retrying."
            db.session.commit()
            raise OfferServiceError(listing.ebay_offer_error)
        listing.ebay_offer_id = offer_id
        listing.ebay_offer_status, listing.ebay_offer_error = "STAGED", None
        listing.ebay_offer_payload_fingerprint = fingerprint
        listing.ebay_offer_staged_at = utcnow()
        if listing.status == ListingStatus.READY:
            listing.transition_to(ListingStatus.EBAY_STAGED)
        db.session.commit()
        return True


def get_offer_service(config=None) -> OfferService:
    if config is None:
        from flask import current_app
        config = current_app.config
    return OfferService(config)
