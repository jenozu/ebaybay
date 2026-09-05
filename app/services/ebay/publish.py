"""Controlled, explicit publication of a previously staged eBay Offer."""
from __future__ import annotations

import requests

from ...extensions import db
from ...models import Listing, ListingStatus, utcnow
from .oauth import OAuthError, get_oauth_service


class PublishServiceError(OAuthError):
    """Safe publish error which never exposes eBay response or token content."""


class PublishService:
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

    def publish_offer(self, listing: Listing) -> bool:
        if listing.status == ListingStatus.PUBLISHED or listing.ebay_listing_id:
            return False
        if listing.status != ListingStatus.EBAY_STAGED or not listing.ebay_offer_id or listing.ebay_offer_status != "STAGED":
            raise PublishServiceError("Stage a valid unpublished eBay offer before publishing.")
        if listing.ebay_publish_status == "UNKNOWN":
            raise PublishServiceError("Publish outcome is unknown. Verify the eBay seller account before trying again.")
        listing.ebay_publish_status, listing.ebay_publish_error = "PUBLISHING", None
        db.session.commit()
        try:
            response = self.http.post(f"{self.base_url}/sell/inventory/v1/offer/{listing.ebay_offer_id}/publish", headers={"Authorization": f"Bearer {self.token_provider()}", "Accept": "application/json"}, timeout=self.config["EBAY_HTTP_TIMEOUT_SECONDS"])
        except requests.RequestException as exc:
            listing.ebay_publish_status, listing.ebay_publish_error = "UNKNOWN", "eBay publish outcome is unknown. Verify eBay before trying again."
            db.session.commit()
            raise PublishServiceError(listing.ebay_publish_error) from exc
        if not getattr(response, "ok", False):
            listing.ebay_publish_status, listing.ebay_publish_error = "FAILED", "eBay could not publish the offer. The unpublished offer and local draft were preserved."
            db.session.commit()
            raise PublishServiceError(listing.ebay_publish_error)
        try:
            payload = response.json()
        except (ValueError, TypeError) as exc:
            listing.ebay_publish_status, listing.ebay_publish_error = "UNKNOWN", "eBay publish outcome is unknown. Verify eBay before trying again."
            db.session.commit()
            raise PublishServiceError(listing.ebay_publish_error) from exc
        listing_id = payload.get("listingId") if isinstance(payload, dict) else None
        if listing_id is None or not str(listing_id):
            listing.ebay_publish_status, listing.ebay_publish_error = "UNKNOWN", "eBay publish outcome is unknown. Verify eBay before trying again."
            db.session.commit()
            raise PublishServiceError(listing.ebay_publish_error)
        listing.ebay_listing_id = str(listing_id)
        listing_url = payload.get("listingUrl") or payload.get("listingWebUrl")
        listing.ebay_listing_url = listing_url if isinstance(listing_url, str) and listing_url else None
        listing.ebay_publish_status, listing.ebay_publish_error = "PUBLISHED", None
        listing.ebay_published_at = utcnow()
        listing.transition_to(ListingStatus.PUBLISHED)
        db.session.commit()
        return True


def get_publish_service(config=None) -> PublishService:
    if config is None:
        from flask import current_app
        config = current_app.config
    return PublishService(config)
