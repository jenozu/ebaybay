from decimal import Decimal

from app.models import Listing
from app.services.ebay.browse import ActiveComparable
from app.services.pricing import ScoredComparable, calculate_pricing, score_comparable, strongest_comparables


def item(item_id, title, price="100", *, currency="CAD", condition="Used", category="123"):
    return ActiveComparable(item_id, title, Decimal(price), Decimal("0"), currency, None, condition, category, "query")


def listing():
    return Listing(mpn="DCF899", brand="DeWalt", model_number="20V", product_name="Impact Wrench", condition="Used", ebay_category_id="123")


def test_similarity_weights_identifiers_condition_category_and_title_overlap():
    exact = score_comparable(listing(), item("1", "DeWalt DCF899 20V Impact Wrench"))
    weak = score_comparable(listing(), item("2", "Generic kitchen spoon", category="999", condition="New"))
    assert exact == 1.0
    assert weak == 0.0


def test_weak_and_wrong_currency_results_are_removed_and_strongest_kept():
    results = strongest_comparables(listing(), [item("weak", "Unrelated thing"), item("usd", "DeWalt DCF899", currency="USD"), item("good", "DeWalt DCF899 Impact Wrench")])
    assert [entry.item.item_id for entry in results] == ["good"]


def test_only_twelve_strongest_comparables_are_kept_deterministically():
    items = [item(str(i), "DeWalt DCF899 Impact Wrench", str(100 + i)) for i in range(15)]
    results = strongest_comparables(listing(), items)
    assert len(results) == 12
    assert [entry.item.item_id for entry in results[:2]] == ["0", "1"]


def test_pricing_targets_range_median_and_medium_confidence():
    comps = [ScoredComparable(item(str(i), "DeWalt DCF899", str(price)), 0.65) for i, price in enumerate([80, 100, 120])]
    summary = calculate_pricing(comps)
    assert (summary.low, summary.high, summary.median) == (Decimal("80.00"), Decimal("120.00"), Decimal("100.00"))
    assert (summary.quick_sale, summary.recommended, summary.high_target) == (Decimal("90.00"), Decimal("100.00"), Decimal("110.00"))
    assert summary.confidence == "MEDIUM"
    assert "3 relevant active listings" in summary.explanation


def test_confidence_is_high_only_with_enough_similar_tightly_priced_results():
    comps = [ScoredComparable(item(str(i), "DeWalt DCF899", str(price)), 0.8) for i, price in enumerate([90, 95, 100, 105, 110])]
    assert calculate_pricing(comps).confidence == "HIGH"
    assert calculate_pricing(comps[:2]).confidence == "LOW"
