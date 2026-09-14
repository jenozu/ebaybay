"""Local, deterministic dashboard grouping for the seller work queue."""
from decimal import Decimal, InvalidOperation

from ..models import Listing, ListingStatus


FILTERS = ("all", "drafts", "attention", "ready", "published")
READY_STATUSES = {ListingStatus.READY, ListingStatus.STAGED, ListingStatus.EBAY_STAGED}
PROBLEM_STATES = {"FAILED", "UNKNOWN"}


def attention_reasons(listing: Listing) -> list[str]:
    """Return actionable reasons using persisted state only (never remote APIs)."""
    if listing.status == ListingStatus.ARCHIVED:
        return []

    reasons = []
    if listing.status == ListingStatus.FAILED:
        reasons.append("Listing workflow failed")
    for label, value in (
        ("Inventory staging", listing.ebay_inventory_status),
        ("Offer staging", listing.ebay_offer_status),
        ("Publishing", listing.ebay_publish_status),
    ):
        if value in PROBLEM_STATES:
            reasons.append(f"{label} needs review")
    if any(image.ebay_upload_status in PROBLEM_STATES for image in listing.images):
        reasons.append("Image upload needs review")

    if listing.status == ListingStatus.DRAFT:
        missing = []
        if not listing.images:
            missing.append("photos")
        if not (listing.title or "").strip():
            missing.append("title")
        if not (listing.condition or "").strip():
            missing.append("condition")
        try:
            if Decimal(str(listing.final_price)) <= 0:
                raise InvalidOperation
        except (InvalidOperation, TypeError):
            missing.append("price")
        if not (listing.ebay_category_id or "").strip():
            missing.append("category")
        if any(aspect.required and not (aspect.value or "").strip() for aspect in listing.aspects):
            missing.append("required item specifics")
        if missing:
            reasons.append("Add " + ", ".join(missing))
    return reasons


def matches_filter(listing: Listing, selected_filter: str, reasons: list[str]) -> bool:
    if selected_filter == "drafts":
        return listing.status == ListingStatus.DRAFT
    if selected_filter == "attention":
        return bool(reasons)
    if selected_filter == "ready":
        return listing.status in READY_STATUSES
    if selected_filter == "published":
        return listing.status == ListingStatus.PUBLISHED
    return True


def build_dashboard_state(listings: list[Listing], selected_filter: str) -> tuple[list[dict], dict[str, int]]:
    selected_filter = selected_filter if selected_filter in FILTERS else "all"
    rows = []
    counts = {"drafts": 0, "attention": 0, "ready": 0, "published": 0}
    for listing in listings:
        reasons = attention_reasons(listing)
        counts["drafts"] += listing.status == ListingStatus.DRAFT
        counts["attention"] += bool(reasons)
        counts["ready"] += listing.status in READY_STATUSES
        counts["published"] += listing.status == ListingStatus.PUBLISHED
        if matches_filter(listing, selected_filter, reasons):
            rows.append({"listing": listing, "attention_reasons": reasons})
    return rows, counts


def connection_health(connection, config: dict) -> dict:
    """Expose only non-sensitive, locally persisted setup state to the template."""
    connected = bool(connection and connection.status == "CONNECTED")
    defaults_ready = bool(
        connected
        and connection.default_payment_policy_id
        and connection.default_fulfillment_policy_id
        and connection.default_return_policy_id
        and connection.default_merchant_location_key
    )
    return {
        "connected": connected,
        "marketplace": config["EBAY_MARKETPLACE_ID"],
        "environment": config["EBAY_ENVIRONMENT"].title(),
        "defaults_ready": defaults_ready,
    }
