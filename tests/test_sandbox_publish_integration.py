"""Opt-in live Sandbox publication through the main application Publish service."""
import os

import pytest

from app.extensions import db
from app.models import Listing, ListingStatus
from app.services.ebay.publish import PublishService


pytestmark = pytest.mark.skipif(os.getenv("RUN_EBAY_SANDBOX_INTEGRATION") != "1", reason="set RUN_EBAY_SANDBOX_INTEGRATION=1 for live Sandbox publish check")


def test_main_app_publish_service_publishes_configured_sandbox_offer(app):
    offer_id = os.getenv("EBAY_SANDBOX_OFFER_ID")
    if not offer_id:
        pytest.skip("set EBAY_SANDBOX_OFFER_ID to a disposable staged Sandbox offer")
    if app.config["EBAY_ENVIRONMENT"] != "sandbox":
        pytest.skip("Sandbox environment is required")
    with app.app_context():
        listing = Listing(sku="SANDBOX-PUBLISH-CHECK", title="Sandbox publish check", condition="Used", quantity=1, status=ListingStatus.EBAY_STAGED, ebay_inventory_status="STAGED", ebay_offer_status="STAGED", ebay_offer_id=offer_id)
        db.session.add(listing); db.session.commit()
        assert PublishService(app.config).publish_offer(listing) is True
        assert listing.status == ListingStatus.PUBLISHED and listing.ebay_listing_id
