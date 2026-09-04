from app.extensions import db
from app.models import Listing, ListingAspect
from app.services.ebay.taxonomy import CategoryAspect, CategoryCandidate


class FakeTaxonomy:
    aspect_calls = []
    def suggest_categories(self, query):
        assert query == "vintage camera lens"
        return [CategoryCandidate("101", "Camera Lenses", "Cameras > Lenses"), CategoryCandidate("102", "Cameras", "Cameras")]
    def get_category_aspects(self, category_id):
        self.aspect_calls.append(category_id)
        return [CategoryAspect("Brand", True, True), CategoryAspect("Focal Length", False, True)]


def make_listing(app):
    with app.app_context():
        listing = Listing(sku="ROUTE-TAX", quantity=1, ai_search_terms=["vintage camera", "lens"], ai_detected_attributes={"Brand": "Canon"})
        db.session.add(listing)
        db.session.commit()
        return listing.id


def test_suggestions_display_select_default_and_persist_aspects(client, login, app, monkeypatch):
    FakeTaxonomy.aspect_calls = []
    listing_id = make_listing(app)
    login()
    monkeypatch.setattr("app.listings._taxonomy_client", FakeTaxonomy)
    response = client.post(f"/listings/{listing_id}/taxonomy/suggest", follow_redirects=True)
    assert response.status_code == 200
    assert b"Top category candidates" in response.data
    assert b"Cameras &gt; Lenses" in response.data
    assert b"Missing required item specifics" not in response.data
    with app.app_context():
        listing = db.session.get(Listing, listing_id)
        assert listing.ebay_category_id == "101"
        assert listing.ebay_category_name == "Camera Lenses"
        assert listing.ebay_category_path == "Cameras > Lenses"
        assert listing.ebay_category_candidates[1]["category_id"] == "102"
        assert {a.name: a.value for a in listing.aspects} == {"Brand": "Canon", "Focal Length": None}


def test_manual_category_override_and_missing_required_flag(client, login, app, monkeypatch):
    FakeTaxonomy.aspect_calls = []
    listing_id = make_listing(app)
    login()
    monkeypatch.setattr("app.listings._taxonomy_client", FakeTaxonomy)
    response = client.post(f"/listings/{listing_id}/taxonomy/category", data={"category_id": "999", "category_name": "Manual", "category_path": "Root > Manual"}, follow_redirects=True)
    assert b"Root &gt; Manual" in response.data
    with app.app_context():
        listing = db.session.get(Listing, listing_id)
        voltage = ListingAspect(listing=listing, name="Voltage", required=True, recommended=True)
        db.session.add(voltage)
        db.session.commit()
        voltage_id = voltage.id
    response = client.get(f"/listings/{listing_id}")
    assert b"Missing required item specifics" in response.data
    assert b"Voltage" in response.data
    client.post(f"/listings/{listing_id}/taxonomy/aspects", data={f"aspect_{voltage_id}": "18 V"})
    with app.app_context():
        assert db.session.get(ListingAspect, voltage_id).value == "18 V"


def test_suggestions_do_not_replace_manual_category(client, login, app, monkeypatch):
    listing_id = make_listing(app)
    with app.app_context():
        listing = db.session.get(Listing, listing_id)
        listing.ebay_category_id, listing.ebay_category_name, listing.ebay_category_path = "777", "Manual", "Manual"
        db.session.commit()
    login()
    monkeypatch.setattr("app.listings._taxonomy_client", FakeTaxonomy)
    client.post(f"/listings/{listing_id}/taxonomy/suggest")
    with app.app_context():
        assert db.session.get(Listing, listing_id).ebay_category_id == "777"
