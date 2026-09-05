from app.models import ComparableListing, Listing, ListingAspect
from app.services.writer import generate_condition_description, generate_description, generate_title


def listing(**kwargs):
    defaults = dict(sku="WRITE-1", quantity=2, brand="Acme", mpn="AX-100", model_number="Model 2", product_name="Acme Precision Widget", condition="Used", seller_notes="Small mark on housing.", ai_visible_observations=["Label is legible"])
    defaults.update(kwargs); return Listing(**defaults)


def test_title_prefers_known_identifiers_and_removes_duplicate_tokens():
    assert generate_title(listing()) == "Acme AX-100 Model 2 Precision Widget"


def test_title_length_boundary_and_unicode_are_deterministic():
    item = listing(brand="Café", mpn="№123", model_number="X" * 90, product_name="Widget")
    title = generate_title(item, 80)
    assert len(title) <= 80 and title == generate_title(item, 80)


def test_title_exact_limit_is_preserved_without_truncation():
    product = "W" * 80
    assert generate_title(listing(brand=None, mpn=None, model_number=None, product_name=product), 80) == product


def test_title_degrades_when_identifiers_are_missing():
    assert generate_title(listing(brand=None, mpn=None, model_number=None, product_name="Widget")) == "Widget"
    assert generate_title(listing(brand=None, mpn=None, model_number=None, product_name=None)) is None


def test_description_uses_grounded_template_escapes_html_and_omits_comparables():
    item = listing(seller_notes="Use <b>carefully</b>")
    item.aspects.append(ListingAspect(name="Color", value="Blue", required=False))
    output = generate_description(item)
    assert "<h2>Item details</h2>" in output and "<h2>Item specifics</h2>" in output
    assert "&lt;b&gt;carefully&lt;/b&gt;" in output
    assert "compatibility" not in output.casefold() and "shipping" not in output.casefold()


def test_comparable_text_cannot_leak_into_generated_copy():
    item = listing()
    item.comparables.append(ComparableListing(title="Rare OEM compatible part with free shipping"))
    generated = (generate_title(item) or "") + (generate_description(item) or "")
    assert "Rare OEM compatible" not in generated


def test_condition_description_uses_only_persisted_condition_notes_observations():
    output = generate_condition_description(listing())
    assert "Condition: Used." in output and "Small mark on housing." in output and "Label is legible" in output
