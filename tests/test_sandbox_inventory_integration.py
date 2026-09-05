"""Opt-in eBay Sandbox Inventory Item staging via the shared OAuth service."""
import os

import pytest

from app.extensions import db
from app.models import Listing, ListingAspect, ListingImage, ListingStatus
from app.services.ebay.inventory import InventoryService


pytestmark = pytest.mark.skipif(os.getenv("RUN_EBAY_SANDBOX_INTEGRATION") != "1", reason="set RUN_EBAY_SANDBOX_INTEGRATION=1 for live Sandbox Inventory check")


def test_main_app_inventory_service_stages_unpublished_sandbox_item(app):
    if app.config["EBAY_ENVIRONMENT"] != "sandbox":
        pytest.skip("Sandbox environment is required")
    with app.app_context():
        listing = Listing(sku="SANDBOX-INVENTORY-CHECK", title="Sandbox inventory check", condition="Used", quantity=1, status=ListingStatus.READY)
        listing.images.append(ListingImage(filename="test.jpg", original_filename="test.jpg", mime_type="image/jpeg", size_bytes=1, ebay_image_url=os.getenv("EBAY_SANDBOX_MEDIA_URL", "")))
        listing.aspects.append(ListingAspect(name="Brand", value="Sandbox", required=True))
        if not listing.images[0].ebay_image_url:
            pytest.skip("set EBAY_SANDBOX_MEDIA_URL to a disposable eBay-hosted Sandbox image")
        db.session.add(listing); db.session.commit()
        assert InventoryService(app.config).stage(listing) is True
        assert listing.ebay_inventory_status == "STAGED" and listing.status == ListingStatus.READY
