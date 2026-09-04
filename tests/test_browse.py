from decimal import Decimal

from app.models import Listing
from app.services.ebay.browse import BrowseClient, SearchTerm, generate_search_terms, search_active_comparables


class FakeResponse:
    def __init__(self, payload): self.payload = payload
    def raise_for_status(self): return None
    def json(self): return self.payload


class FakeSession:
    def __init__(self, payload): self.payload, self.calls = payload, []
    def get(self, url, **kwargs): self.calls.append((url, kwargs)); return FakeResponse(self.payload)


def test_search_terms_have_identifier_first_and_deterministic_fallbacks():
    listing = Listing(mpn="DCF899", brand="DeWalt", model_number="20V Max", product_name="Impact Wrench", ai_search_terms=["DeWalt wrench", "DeWalt wrench"])
    terms = generate_search_terms(listing)
    assert [(t.query, t.strategy) for t in terms] == [
        ("DCF899", "exact_mpn"), ("DeWalt DCF899", "brand_mpn"), ("DeWalt 20V Max", "brand_model"),
        ("DeWalt wrench", "ai_term"), ("DeWalt Impact Wrench", "broad"),
    ]


def test_brand_model_and_broad_work_without_mpn():
    listing = Listing(brand="Canon", model_number="AE-1", product_name="Film Camera")
    assert [(t.query, t.strategy) for t in generate_search_terms(listing)] == [("Canon AE-1", "brand_model"), ("Canon Film Camera", "broad")]


def test_browse_normalizes_active_listing_shipping_and_currency():
    session = FakeSession({"itemSummaries": [{"itemId": "v1|1|0", "title": "DeWalt DCF899", "price": {"value": "99.9", "currency": "cad"}, "shippingOptions": [{"shippingCost": {"value": "12.345", "currency": "CAD"}}], "condition": "Used", "categories": [{"categoryId": "123"}], "itemWebUrl": "https://example.test/item"}]})
    client = BrowseClient(environment="sandbox", marketplace_id="EBAY_CA", access_token_provider=lambda: "token", session=session)
    item = client.search(SearchTerm("DCF899", "exact_mpn"))[0]
    assert (item.price, item.shipping_cost, item.total_price, item.currency) == (Decimal("99.90"), Decimal("12.35"), Decimal("112.25"), "CAD")
    assert item.category_id == "123"
    assert session.calls[0][1]["params"]["filter"] == "buyingOptions:{FIXED_PRICE}"
    assert session.calls[0][1]["headers"]["X-EBAY-C-MARKETPLACE-ID"] == "EBAY_CA"


def test_broad_fallback_runs_only_until_enough_unique_results():
    class Client:
        def __init__(self): self.calls = []
        def search(self, term):
            self.calls.append(term.strategy)
            return []
    listing = Listing(mpn="X", brand="Brand", model_number="M", product_name="Widget", ai_search_terms=["other widget"])
    client = Client()
    search_active_comparables(listing, client)
    assert client.calls == ["exact_mpn", "brand_mpn", "brand_model", "ai_term", "broad"]


def test_broad_fallback_runs_when_specific_results_are_not_relevant():
    class Client:
        def __init__(self): self.calls = []
        def search(self, term):
            self.calls.append(term.strategy)
            return [type("Item", (), {"item_id": f"{term.strategy}-{i}"})() for i in range(6)]
    listing = Listing(mpn="X", brand="Brand", model_number="M", product_name="Widget", ai_search_terms=["other widget"])
    client = Client()
    search_active_comparables(listing, client, relevance_filter=lambda items: [])
    assert client.calls[-2:] == ["ai_term", "broad"]
