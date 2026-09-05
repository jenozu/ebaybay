"""Opt-in Sandbox Offer staging with existing Inventory Item and seller defaults."""
import os

import pytest

from app.extensions import db
from app.models import Listing, ListingStatus
from app.services.ebay.offers import OfferService


pytestmark = pytest.mark.skipif(os.getenv("RUN_EBAY_SANDBOX_INTEGRATION") != "1", reason="set RUN_EBAY_SANDBOX_INTEGRATION=1 for live Sandbox Offer check")


def test_main_app_offer_service_creates_unpublished_sandbox_offer(app):
    if app.config["EBAY_ENVIRONMENT"] != "sandbox":
        pytest.skip("Sandbox environment is required")
    with app.app_context():
        listing = Listing(sku="SANDBOX-OFFER-CHECK", title="Sandbox offer check", description="Disposable Sandbox offer verification.", condition="Used", quantity=1, final_price="1.00", ebay_category_id=os.getenv("EBAY_SANDBOX_CATEGORY_ID", ""), ebay_inventory_status="STAGED", status=ListingStatus.READY)
        if not listing.ebay_category_id:
            pytest.skip("set EBAY_SANDBOX_CATEGORY_ID to a valid Sandbox category")
        db.session.add(listing); db.session.commit()
        assert OfferService(app.config).stage(listing) is True
        assert listing.ebay_offer_id and listing.status == ListingStatus.EBAY_STAGED
