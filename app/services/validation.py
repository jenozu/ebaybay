"""Reusable deterministic validation for listing approval and later staging."""
from dataclasses import dataclass
from decimal import Decimal, InvalidOperation
from pathlib import Path

from ..models import Listing
from .ebay.oauth import get_oauth_service


@dataclass(frozen=True)
class ValidationIssue:
    field: str
    message: str
    severity: str = "error"


def validate_listing(listing: Listing, *, config: dict, upload_dir: Path, sku_exists) -> list[ValidationIssue]:
    issues: list[ValidationIssue] = []
    def required(value, field, message):
        if value in (None, ""):
            issues.append(ValidationIssue(field, message))

    if not listing.images:
        issues.append(ValidationIssue("images", "Add at least one image before approval."))
    elif any(not (upload_dir / image.filename).is_file() for image in listing.images):
        issues.append(ValidationIssue("images", "One or more saved listing images are unavailable."))
    required(listing.title, "title", "Add a listing title.")
    if listing.title and len(listing.title) > config["EBAY_TITLE_MAX_LENGTH"]:
        issues.append(ValidationIssue("title", f"Title must be {config['EBAY_TITLE_MAX_LENGTH']} characters or fewer."))
    required(listing.condition, "condition", "Select an item condition.")
    if not isinstance(listing.quantity, int) or listing.quantity <= 0:
        issues.append(ValidationIssue("quantity", "Quantity must be greater than zero."))
    try:
        price = Decimal(str(listing.final_price))
        if price <= 0: raise InvalidOperation
        if price.as_tuple().exponent < -2:
            issues.append(ValidationIssue("final_price", "Final price cannot use more than two decimal places."))
    except (InvalidOperation, TypeError):
        issues.append(ValidationIssue("final_price", "Set a final price greater than zero."))
    required(listing.ebay_category_id, "category", "Select an eBay category.")
    if not listing.sku or sku_exists(listing.sku, listing.id):
        issues.append(ValidationIssue("sku", "SKU must be unique."))
    for aspect in listing.aspects:
        if aspect.required and not (aspect.value or "").strip():
            issues.append(ValidationIssue("aspects", f"Required item specific is missing: {aspect.name}."))
    for key, label in (("EBAY_PAYMENT_POLICY_ID", "payment policy"), ("EBAY_FULFILLMENT_POLICY_ID", "fulfillment policy"), ("EBAY_RETURN_POLICY_ID", "return policy"), ("EBAY_MERCHANT_LOCATION_KEY", "inventory location"), ("EBAY_MARKETPLACE_ID", "marketplace")):
        required(config.get(key), key.lower(), f"Configure a {label} before approval.")
    if config.get("EBAY_LISTING_FORMAT") not in {"FIXED_PRICE", "AUCTION"}:
        issues.append(ValidationIssue("listing_format", "Listing format must be FIXED_PRICE or AUCTION."))
    if not get_oauth_service(config).has_usable_connection():
        issues.append(ValidationIssue("oauth", "A usable saved eBay OAuth access token is required before approval."))
    return issues
