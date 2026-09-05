"""Staging of approved drafts as unpublished eBay Inventory Items."""
from __future__ import annotations

import hashlib
import json

import requests

from ...extensions import db
from ...models import Listing, ListingStatus, utcnow
from .oauth import OAuthError, get_oauth_service


class InventoryServiceError(OAuthError):
    """Safe Inventory API failure that does not expose API response content."""


_CONDITIONS = {
    "new": "NEW", "used": "USED_EXCELLENT", "used - excellent": "USED_EXCELLENT",
    "used - very good": "USED_VERY_GOOD", "used - good": "USED_GOOD",
    "used - acceptable": "USED_ACCEPTABLE", "seller refurbished": "SELLER_REFURBISHED",
    "certified refurbished": "CERTIFIED_REFURBISHED", "for parts or not working": "FOR_PARTS_OR_NOT_WORKING",
}


def inventory_condition(value: str | None) -> str | None:
    """Map familiar local condition labels to Inventory API condition enums."""
    if not value:
        return None
    normalized = " ".join(value.split()).casefold()
    return _CONDITIONS.get(normalized, value.strip().upper().replace(" ", "_"))


def inventory_payload(listing: Listing) -> dict:
    """Build the smallest factual Inventory Item payload; this does not create an offer."""
    ordered_images = sorted(listing.images, key=lambda image: image.sort_order)
    if not ordered_images or any(not image.ebay_image_url for image in ordered_images):
        raise InventoryServiceError("Upload every listing image to eBay before staging inventory.")
    image_urls = [image.ebay_image_url for image in ordered_images]
    condition = inventory_condition(listing.condition)
    if not condition:
        raise InventoryServiceError("Select a valid item condition before staging inventory.")
    aspects = {aspect.name: [aspect.value.strip()] for aspect in listing.aspects if aspect.name and (aspect.value or "").strip()}
    product = {"title": listing.title, "imageUrls": image_urls, "aspects": aspects}
    if listing.description:
        product["description"] = listing.description
    if listing.brand:
        product["brand"] = listing.brand
    if listing.mpn:
        product["mpn"] = listing.mpn
    if listing.gtin:
        product["ean"] = [listing.gtin]
    return {
        "availability": {"shipToLocationAvailability": {"quantity": listing.quantity}},
        "condition": condition,
        "product": product,
    }


class InventoryService:
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
        if listing.status != ListingStatus.READY:
            raise InventoryServiceError("Only an approved READY listing can be staged as eBay inventory.")
        payload = inventory_payload(listing)
        fingerprint = hashlib.sha256(json.dumps(payload, sort_keys=True, separators=(",", ":")).encode()).hexdigest()
        if listing.ebay_inventory_status == "STAGED" and listing.ebay_inventory_payload_fingerprint == fingerprint:
            return False
        listing.ebay_inventory_status, listing.ebay_inventory_error = "STAGING", None
        db.session.commit()
        try:
            response = self.http.put(
                f"{self.base_url}/sell/inventory/v1/inventory_item/{listing.sku}", json=payload,
                headers={"Authorization": f"Bearer {self.token_provider()}", "Content-Type": "application/json", "Accept": "application/json"},
                timeout=self.config["EBAY_HTTP_TIMEOUT_SECONDS"],
            )
        except requests.RequestException as exc:
            listing.ebay_inventory_status, listing.ebay_inventory_error = "FAILED", "eBay inventory staging was temporarily unavailable."
            db.session.commit()
            raise InventoryServiceError(listing.ebay_inventory_error) from exc
        if not getattr(response, "ok", False):
            listing.ebay_inventory_status, listing.ebay_inventory_error = "FAILED", "eBay rejected the inventory item. Review the listing details and try again."
            db.session.commit()
            raise InventoryServiceError(listing.ebay_inventory_error)
        listing.ebay_inventory_status = "STAGED"
        listing.ebay_inventory_error = None
        listing.ebay_inventory_payload_fingerprint = fingerprint
        listing.ebay_inventory_staged_at = utcnow()
        db.session.commit()
        return True


def get_inventory_service(config=None) -> InventoryService:
    if config is None:
        from flask import current_app
        config = current_app.config
    return InventoryService(config)
