from decimal import Decimal

from app.extensions import db
from app.models import Listing, ListingAspect, ListingImage, ListingStatus
from app.services.validation import validate_listing
from app.services.ebay.oauth import OAuthService


def ready_config(app, tmp_path):
    app.config.update(EBAY_LISTING_FORMAT="FIXED_PRICE")
    connection = OAuthService(app.config).save_token_response({"access_token": "test", "refresh_token": "refresh", "expires_in": 7200}, require_refresh=True)
    connection.default_payment_policy_id = "pay"; connection.default_fulfillment_policy_id = "ship"; connection.default_return_policy_id = "returns"; connection.default_merchant_location_key = "warehouse"
    connection.seller_defaults_cache = {"payment_policies": [{"policy_id": "pay"}], "fulfillment_policies": [{"policy_id": "ship"}], "return_policies": [{"policy_id": "returns"}], "inventory_locations": [{"merchant_location_key": "warehouse", "selectable": True}]}
    db.session.commit()


def valid_listing(app):
    listing = Listing(sku="VALID-1", title="Acme AX-1 Widget", condition="Used", quantity=1, final_price=Decimal("10.00"), ebay_category_id="123")
    path = app.config["UPLOAD_DIR"] / "valid.jpg"; path.write_bytes(b"image")
    listing.images.append(ListingImage(filename="valid.jpg", original_filename="valid.jpg", mime_type="image/jpeg", size_bytes=5))
    listing.aspects.append(ListingAspect(name="Brand", value="Acme", required=True))
    db.session.add(listing); db.session.commit(); return listing


def validate(app, listing):
    return validate_listing(listing, config=app.config, upload_dir=app.config["UPLOAD_DIR"], sku_exists=lambda sku, listing_id: db.session.query(Listing).filter(Listing.sku == sku, Listing.id != listing_id).first() is not None)


def test_valid_listing_has_no_blockers(app, tmp_path):
    with app.app_context():
        ready_config(app, tmp_path); assert validate(app, valid_listing(app)) == []


def test_validation_returns_specific_errors_for_missing_requirements(app, tmp_path):
    with app.app_context():
        ready_config(app, tmp_path)
        listing = Listing(sku="BAD", quantity=0); db.session.add(listing); db.session.commit()
        listing.final_price = Decimal("1.999")
        messages = {issue.field: issue.message for issue in validate(app, listing)}
        assert {"images", "title", "condition", "quantity", "final_price", "category"} <= messages.keys()


def test_required_aspect_policy_and_oauth_are_blockers(app, tmp_path):
    with app.app_context():
        listing = valid_listing(app); listing.aspects[0].value = None
        app.config.update(EBAY_TOKEN_PATH=tmp_path / "missing.json")
        fields = {issue.field for issue in validate(app, listing)}
        assert {"aspects", "ebay_payment_policy_id", "ebay_fulfillment_policy_id", "ebay_return_policy_id", "ebay_merchant_location_key", "oauth"} <= fields


def test_duplicate_sku_and_missing_image_file_are_blockers(app, tmp_path):
    with app.app_context():
        ready_config(app, tmp_path); listing = valid_listing(app)
        (app.config["UPLOAD_DIR"] / "valid.jpg").unlink()
        fields = {issue.field for issue in validate_listing(listing, config=app.config, upload_dir=app.config["UPLOAD_DIR"], sku_exists=lambda *_: True)}
        assert "images" in fields and "sku" in fields
