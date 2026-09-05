from app.extensions import db
from app.models import Listing, ListingAspect


def make_listing(app, *, title=None, title_manual=False):
    with app.app_context():
        listing = Listing(sku="WRITE-ROUTE", quantity=1, title=title, title_manual=title_manual, brand="Acme", mpn="AX-1", product_name="Widget", condition="Used", seller_notes="Known scratch")
        listing.aspects.append(ListingAspect(name="Color", value="Blue"))
        db.session.add(listing); db.session.commit(); return listing.id


def test_generated_copy_persists_and_is_visible_editable(client, login, app):
    listing_id = make_listing(app); login()
    for field in ("title", "description", "condition_description"):
        response = client.post(f"/listings/{listing_id}/copy/regenerate/{field}", follow_redirects=True)
        assert response.status_code == 200
    assert b"Regenerate Title" in response.data and b"Generated copy" in response.data
    with app.app_context():
        listing = db.session.get(Listing, listing_id)
        assert listing.title == "Acme AX-1 Widget" and "Item specifics" in listing.description and listing.condition_description


def test_manual_copy_is_preserved_until_explicit_replace(client, login, app):
    listing_id = make_listing(app, title="Manual listing title", title_manual=True); login()
    response = client.post(f"/listings/{listing_id}/copy/regenerate/title", follow_redirects=True)
    assert b"Manual title was preserved" in response.data
    client.post(f"/listings/{listing_id}/copy/regenerate/title", data={"replace_manual": "1"})
    with app.app_context():
        listing = db.session.get(Listing, listing_id)
        assert listing.title == "Acme AX-1 Widget" and listing.title_manual is False


def test_manual_description_and_condition_edits_are_preserved(client, login, app):
    listing_id = make_listing(app); login()
    client.post(f"/listings/{listing_id}/copy/save", data={"description": "Manual desc", "original_description": "", "condition_description": "Manual condition", "original_condition_description": ""})
    client.post(f"/listings/{listing_id}/copy/regenerate/description")
    client.post(f"/listings/{listing_id}/copy/regenerate/condition_description")
    with app.app_context():
        listing = db.session.get(Listing, listing_id)
        assert listing.description == "Manual desc" and listing.condition_description == "Manual condition"
        assert listing.description_manual and listing.condition_description_manual


def test_copy_routes_are_protected(client, app):
    listing_id = make_listing(app)
    response = client.post(f"/listings/{listing_id}/copy/regenerate/title")
    assert response.status_code == 302 and "/login" in response.headers["Location"]


def test_copy_save_rejects_over_limit_manual_title(client, login, app):
    listing_id = make_listing(app); login()
    response = client.post(f"/listings/{listing_id}/copy/save", data={"title": "x" * 81, "original_title": ""}, follow_redirects=True)
    assert b"80 characters or fewer" in response.data
    with app.app_context(): assert db.session.get(Listing, listing_id).title is None
