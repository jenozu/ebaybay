from decimal import Decimal

from app.extensions import db
from app.models import Listing
from app.services.ebay.browse import ActiveComparable, BrowseError


class FakeBrowse:
    def search(self, term):
        base = [90, 95, 100, 105, 110]
        return [ActiveComparable(str(i), f"DeWalt DCF899 20V Impact Wrench {i}", Decimal(str(price)), Decimal("10"), "CAD", f"https://example.test/{i}", "Used", "123", term.query) for i, price in enumerate(base)]


def make_listing(app, *, final_price=None, manual=False):
    with app.app_context():
        listing = Listing(sku="COMP-1", quantity=1, brand="DeWalt", mpn="DCF899", model_number="20V", product_name="Impact Wrench", condition="Used", ebay_category_id="123", final_price=final_price, final_price_manual=manual)
        db.session.add(listing); db.session.commit(); return listing.id


def test_refresh_persists_strongest_comparables_pricing_and_active_label(client, login, app, monkeypatch):
    listing_id = make_listing(app)
    login(); monkeypatch.setattr("app.listings._browse_client", FakeBrowse)
    response = client.post(f"/listings/{listing_id}/comparables/refresh", follow_redirects=True)
    assert response.status_code == 200
    assert b"Active Comparables" in response.data
    assert b"not sold or completed sales" in response.data
    assert b"Recommended" in response.data and b"Quick sale" in response.data and b"High target" in response.data
    with app.app_context():
        listing = db.session.get(Listing, listing_id)
        assert len(listing.comparables) == 5
        assert listing.comparables[0].shipping_cost == Decimal("10.00")
        assert listing.comparable_median == Decimal("110.00")
        assert listing.recommended_price == Decimal("110.00")
        assert listing.final_price == Decimal("110.00")
        assert listing.pricing_confidence == "HIGH"


def test_refresh_preserves_manual_final_price(client, login, app, monkeypatch):
    listing_id = make_listing(app, final_price=Decimal("149.99"), manual=True)
    login(); monkeypatch.setattr("app.listings._browse_client", FakeBrowse)
    client.post(f"/listings/{listing_id}/comparables/refresh")
    with app.app_context():
        listing = db.session.get(Listing, listing_id)
        assert listing.final_price == Decimal("149.99")
        assert listing.recommended_price == Decimal("110.00")


def test_editing_price_sets_manual_override_and_unrelated_edit_preserves_default_state(client, login, app):
    listing_id = make_listing(app, final_price=Decimal("100"), manual=False)
    login()
    client.post(f"/listings/{listing_id}/edit", data={"quantity": "1", "title": "Changed", "final_price": "100.00", "original_final_price": "100.00"})
    with app.app_context(): assert db.session.get(Listing, listing_id).final_price_manual is False
    client.post(f"/listings/{listing_id}/edit", data={"quantity": "1", "final_price": "125.00", "original_final_price": "100.00"})
    with app.app_context():
        listing = db.session.get(Listing, listing_id)
        assert listing.final_price == Decimal("125.00") and listing.final_price_manual is True


def test_browse_error_is_shown_and_existing_data_is_preserved(client, login, app, monkeypatch):
    class BrokenBrowse:
        def search(self, term): raise BrowseError("provider unavailable")
    listing_id = make_listing(app, final_price=Decimal("149.99"), manual=True)
    login(); monkeypatch.setattr("app.listings._browse_client", BrokenBrowse)
    response = client.post(f"/listings/{listing_id}/comparables/refresh", follow_redirects=True)
    assert b"provider unavailable" in response.data
    with app.app_context(): assert db.session.get(Listing, listing_id).final_price == Decimal("149.99")
