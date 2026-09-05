from decimal import Decimal

from app.extensions import db
from app.models import Listing, ListingImage, ListingStatus
from app.services.validation import validate_listing
from app.services.ebay.oauth import OAuthService


def setup_valid(app, tmp_path):
    app.config.update(EBAY_PAYMENT_POLICY_ID="pay", EBAY_FULFILLMENT_POLICY_ID="ship", EBAY_RETURN_POLICY_ID="returns", EBAY_MERCHANT_LOCATION_KEY="warehouse")
    with app.app_context():
        OAuthService(app.config).save_token_response({"access_token": "test", "refresh_token": "refresh", "expires_in": 7200}, require_refresh=True)
        listing = Listing(sku="APPROVE-1", title="Acme Widget", condition="Used", quantity=1, final_price=Decimal("10.00"), ebay_category_id="123")
        path = app.config["UPLOAD_DIR"] / "approval.jpg"; path.write_bytes(b"x")
        listing.images.append(ListingImage(filename="approval.jpg", original_filename="approval.jpg", mime_type="image/jpeg", size_bytes=1))
        db.session.add(listing); db.session.commit(); return listing.id


def test_invalid_listing_cannot_be_approved(client, login, app):
    with app.app_context(): db.session.add(Listing(sku="BAD-APPROVE", quantity=1)); db.session.commit(); listing_id = db.session.query(Listing.id).scalar()
    login(); response = client.post(f"/listings/{listing_id}/approve", follow_redirects=True)
    assert b"cannot be approved" in response.data
    with app.app_context(): assert db.session.get(Listing, listing_id).status == ListingStatus.DRAFT


def test_valid_listing_requires_explicit_approval_and_can_return_to_draft(client, login, app, tmp_path):
    listing_id = setup_valid(app, tmp_path); login()
    with app.app_context():
        listing = db.session.get(Listing, listing_id)
        assert validate_listing(listing, config=app.config, upload_dir=app.config["UPLOAD_DIR"], sku_exists=lambda *_: False) == []
    client.post(f"/listings/{listing_id}/validate")
    with app.app_context(): assert db.session.get(Listing, listing_id).status == ListingStatus.DRAFT
    response = client.post(f"/listings/{listing_id}/approve", follow_redirects=True)
    assert b"approved and marked READY" in response.data
    with app.app_context(): assert db.session.get(Listing, listing_id).status == ListingStatus.READY
    client.post(f"/listings/{listing_id}/return-to-draft")
    with app.app_context(): assert db.session.get(Listing, listing_id).status == ListingStatus.DRAFT


def test_material_edit_invalidates_approval(client, login, app, tmp_path):
    listing_id = setup_valid(app, tmp_path); login(); client.post(f"/listings/{listing_id}/approve")
    client.post(f"/listings/{listing_id}/copy/save", data={"title": "Changed title", "original_title": "Acme Widget"})
    with app.app_context(): assert db.session.get(Listing, listing_id).status == ListingStatus.DRAFT


def test_ai_analysis_is_blocked_while_listing_is_approved(client, login, app, tmp_path):
    listing_id = setup_valid(app, tmp_path); login(); client.post(f"/listings/{listing_id}/approve")
    response = client.post(f"/listings/{listing_id}/analyze", follow_redirects=True)
    assert b"Return an approved listing to DRAFT" in response.data
    with app.app_context(): assert db.session.get(Listing, listing_id).status == ListingStatus.READY


def test_approval_routes_are_protected(client, app, tmp_path):
    listing_id = setup_valid(app, tmp_path)
    response = client.post(f"/listings/{listing_id}/approve")
    assert response.status_code == 302 and "/login" in response.headers["Location"]
