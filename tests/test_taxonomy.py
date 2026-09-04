from app.extensions import db
from app.models import Listing, ListingAspect
from app.services.ebay.taxonomy import CategoryAspect, CategoryCandidate, TaxonomyClient, select_category, sync_listing_aspects, taxonomy_query


class FakeResponse:
    def __init__(self, payload): self.payload = payload
    def raise_for_status(self): return None
    def json(self): return self.payload


class FakeSession:
    def __init__(self, responses): self.responses, self.calls = iter(responses), []
    def get(self, url, **kwargs):
        self.calls.append((url, kwargs))
        return FakeResponse(next(self.responses))


def test_taxonomy_client_normalizes_candidates_and_caches_tree():
    TaxonomyClient._tree_cache.clear()
    session = FakeSession([
        {"categoryTreeId": "2"},
        {"categorySuggestions": [{"category": {"categoryId": "123", "categoryName": "Impact Wrenches"}, "categoryTreeNodeAncestors": [{"categoryName": "Tools"}, {"categoryName": "Home & Garden"}]}]},
        {"categorySuggestions": []},
    ])
    client = TaxonomyClient(environment="sandbox", marketplace_id="EBAY_CA", access_token_provider=lambda: "token", session=session)
    result = client.suggest_categories("DeWalt wrench")
    client.suggest_categories("another")
    assert result == [CategoryCandidate("123", "Impact Wrenches", "Home & Garden > Tools > Impact Wrenches")]
    assert sum("get_default_category_tree_id" in call[0] for call in session.calls) == 1
    assert session.calls[1][1]["params"] == {"q": "DeWalt wrench"}


def test_taxonomy_client_identifies_required_and_recommended_aspects():
    TaxonomyClient._tree_cache.clear()
    session = FakeSession([
        {"categoryTreeId": "2"},
        {"aspects": [
            {"localizedAspectName": "Brand", "aspectConstraint": {"aspectRequired": True, "aspectUsage": "RECOMMENDED"}},
            {"localizedAspectName": "Color", "aspectConstraint": {"aspectRequired": False, "aspectUsage": "RECOMMENDED"}},
            {"localizedAspectName": "Optional Detail", "aspectConstraint": {"aspectRequired": False}},
        ]},
    ])
    client = TaxonomyClient(environment="sandbox", marketplace_id="EBAY_CA", access_token_provider=lambda: "token", session=session)
    assert client.get_category_aspects("123") == [CategoryAspect("Brand", True, True), CategoryAspect("Color", False, True)]


def test_ai_terms_and_attributes_enrich_without_overwriting_manual_values(app):
    with app.app_context():
        listing = Listing(sku="TAX-1", quantity=1, brand="Fallback", ai_search_terms=["DeWalt DCF899", "impact wrench"], ai_detected_attributes={"brand": "DeWalt", "Color": "Yellow"})
        listing.aspects.append(ListingAspect(name="Brand", value="Manually corrected"))
        db.session.add(listing)
        sync_listing_aspects(listing, [CategoryAspect("Brand", True, True), CategoryAspect("Color", False, True), CategoryAspect("Voltage", True, True)])
        assert taxonomy_query(listing) == "DeWalt DCF899 impact wrench"
        assert {a.name: a.value for a in listing.aspects} == {"Brand": "Manually corrected", "Color": "Yellow", "Voltage": None}
        assert [a.name for a in listing.aspects if a.required and not a.value] == ["Voltage"]


def test_select_category_fetches_aspects_only_when_category_changes(app):
    class FakeTaxonomy:
        calls = []
        def get_category_aspects(self, category_id):
            self.calls.append(category_id)
            return [CategoryAspect("Brand", True, True)]
    with app.app_context():
        listing = Listing(sku="TAX-2", quantity=1, ai_detected_attributes={"Brand": "Makita"})
        client = FakeTaxonomy()
        candidate = CategoryCandidate("456", "Drills", "Tools > Drills")
        select_category(listing, client, candidate)
        select_category(listing, client, candidate)
        assert client.calls == ["456"]
        assert listing.ebay_category_path == "Tools > Drills"
        assert listing.aspects[0].value == "Makita"
