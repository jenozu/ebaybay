"""Staging of approved drafts as unpublished eBay Inventory Items."""
from __future__ import annotations

import hashlib
import json
import logging
from urllib.parse import quote

import requests

from ...extensions import db
from ...models import Listing, ListingStatus, utcnow
from .oauth import OAuthError, get_oauth_service


logger = logging.getLogger(__name__)


class InventoryServiceError(OAuthError):
    """Safe Inventory API failure that does not expose API response content."""


_CONDITIONS = {
    "new": "NEW", "used": "USED_EXCELLENT", "used - excellent": "USED_EXCELLENT",
    "used - very good": "USED_VERY_GOOD", "used - good": "USED_GOOD",
    "used - acceptable": "USED_ACCEPTABLE", "seller refurbished": "SELLER_REFURBISHED",
    "certified refurbished": "CERTIFIED_REFURBISHED", "for parts or not working": "FOR_PARTS_OR_NOT_WORKING",
}

_PRODUCT_IDENTIFIER_ERROR = (
    "GTIN must be a valid UPC-12, EAN-8/EAN-13, ISBN-10/ISBN-13, or left blank."
)
_SAFE_ERROR_FIELDS = ("errorId", "domain", "category", "message")
_SAFE_ERROR_TEXT_LIMIT = 300


def inventory_condition(value: str | None) -> str | None:
    """Map familiar local condition labels to Inventory API condition enums."""
    if not value:
        return None
    normalized = " ".join(value.split()).casefold()
    return _CONDITIONS.get(normalized, value.strip().upper().replace(" ", "_"))


def _numeric_gtin_checksum_is_valid(value: str) -> bool:
    if not value.isdigit() or len(value) < 2:
        return False
    total = 0
    for position, digit in enumerate(reversed(value[:-1]), start=1):
        total += int(digit) * (3 if position % 2 else 1)
    expected = (10 - (total % 10)) % 10
    return expected == int(value[-1])


def _isbn10_checksum_is_valid(value: str) -> bool:
    if len(value) != 10 or not value[:9].isdigit() or not (value[-1].isdigit() or value[-1] == "X"):
        return False
    digits = [int(char) for char in value[:9]] + [10 if value[-1] == "X" else int(value[-1])]
    return sum((10 - index) * digit for index, digit in enumerate(digits)) % 11 == 0


def product_identifier(value: str | None) -> tuple[str, str] | None:
    """Return the Inventory API product identifier field and normalized value."""
    if value is None or not value.strip():
        return None
    normalized = value.strip().upper().replace(" ", "").replace("-", "")
    if len(normalized) == 10 and _isbn10_checksum_is_valid(normalized):
        return "isbn", normalized
    if normalized.isdigit() and len(normalized) in {8, 12, 13} and _numeric_gtin_checksum_is_valid(normalized):
        if len(normalized) == 12:
            return "upc", normalized
        if len(normalized) == 13 and normalized.startswith(("978", "979")):
            return "isbn", normalized
        return "ean", normalized
    raise ValueError(_PRODUCT_IDENTIFIER_ERROR)


def _safe_error_text(value) -> str | None:
    if value is None or isinstance(value, (dict, list, tuple, set)):
        return None
    text = " ".join(str(value).split())
    return text[:_SAFE_ERROR_TEXT_LIMIT] or None


def safe_ebay_error_details(response) -> dict[str, str | int]:
    """Extract only non-secret, diagnostic eBay error fields from an HTTP response."""
    details: dict[str, str | int] = {}
    status = getattr(response, "status_code", None)
    if isinstance(status, int):
        details["status"] = status
    try:
        payload = response.json()
    except (AttributeError, TypeError, ValueError):
        return details
    if not isinstance(payload, dict):
        return details
    errors = payload.get("errors")
    if not isinstance(errors, list) or not errors or not isinstance(errors[0], dict):
        return details
    error = errors[0]
    for field in _SAFE_ERROR_FIELDS:
        value = _safe_error_text(error.get(field))
        if value is not None:
            details[field] = value
    return details


def _safe_rejection_message(details: dict[str, str | int]) -> str:
    message = "eBay rejected the inventory item."
    diagnostic_bits = []
    if details.get("status") is not None:
        diagnostic_bits.append(f"HTTP {details['status']}")
    if details.get("errorId"):
        diagnostic_bits.append(f"eBay error {details['errorId']}")
    if details.get("message"):
        diagnostic_bits.append(str(details["message"]))
    if diagnostic_bits:
        message = f"{message} {' · '.join(diagnostic_bits)}"
    return message


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
    try:
        identifier = product_identifier(listing.gtin)
    except ValueError as exc:
        raise InventoryServiceError(str(exc)) from exc
    if identifier:
        field, normalized = identifier
        product[field] = [normalized]
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

    def _headers(self) -> dict[str, str]:
        headers = {
            "Authorization": f"Bearer {self.token_provider()}",
            "Content-Type": "application/json",
            "Accept": "application/json",
        }
        # EBAY_CA supports both English and French. This app targets the
        # English Canadian storefront, so localized Inventory text must be
        # explicitly identified as en-CA.
        if self.config.get("EBAY_MARKETPLACE_ID") == "EBAY_CA":
            headers["Content-Language"] = "en-CA"
            headers["Accept-Language"] = "en-CA"
        return headers

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
                f"{self.base_url}/sell/inventory/v1/inventory_item/{quote(listing.sku, safe='')}",
                json=payload,
                headers=self._headers(),
                timeout=self.config["EBAY_HTTP_TIMEOUT_SECONDS"],
            )
        except requests.RequestException as exc:
            listing.ebay_inventory_status, listing.ebay_inventory_error = "FAILED", "eBay inventory staging was temporarily unavailable."
            db.session.commit()
            raise InventoryServiceError(listing.ebay_inventory_error) from exc
        if not getattr(response, "ok", False):
            details = safe_ebay_error_details(response)
            logger.warning("eBay Inventory API rejected request: %s", json.dumps(details, sort_keys=True))
            listing.ebay_inventory_status = "FAILED"
            listing.ebay_inventory_error = _safe_rejection_message(details)
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
