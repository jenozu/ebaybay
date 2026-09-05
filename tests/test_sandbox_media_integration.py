"""Opt-in Media API verification using the shared application OAuth service."""
import os
from pathlib import Path

import pytest

from app.extensions import db
from app.models import Listing, ListingImage, ListingStatus
from app.services.ebay.media import MediaService


pytestmark = pytest.mark.skipif(os.getenv("RUN_EBAY_SANDBOX_INTEGRATION") != "1", reason="set RUN_EBAY_SANDBOX_INTEGRATION=1 for live Sandbox Media API check")


def test_main_app_media_service_uploads_configured_sandbox_test_image(app):
    image_path = os.getenv("EBAY_SANDBOX_MEDIA_TEST_IMAGE")
    if not image_path or not Path(image_path).is_file():
        pytest.skip("set EBAY_SANDBOX_MEDIA_TEST_IMAGE to a disposable local image")
    if app.config["EBAY_ENVIRONMENT"] != "sandbox":
        pytest.skip("Sandbox environment is required")
    with app.app_context():
        source = Path(image_path)
        target = app.config["UPLOAD_DIR"] / source.name
        target.write_bytes(source.read_bytes())
        listing = Listing(sku="SANDBOX-MEDIA-CHECK", status=ListingStatus.READY, quantity=1)
        listing.images.append(ListingImage(filename=target.name, original_filename=source.name, mime_type="image/jpeg", size_bytes=target.stat().st_size, sort_order=0))
        db.session.add(listing); db.session.commit()
        uploaded, _ = MediaService(app.config).upload_listing_images(listing, app.config["UPLOAD_DIR"])
        assert uploaded == 1 and listing.images[0].ebay_image_id and listing.images[0].ebay_image_url
