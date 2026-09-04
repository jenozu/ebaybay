import json

import pytest

from app.ai.prompts import SYSTEM_PROMPT, build_user_prompt
from app.ai.providers.base import AIImage, AIProvider, ProviderResult
from app.ai.service import AnalysisValidationError, analyze_listing, parse_analysis
from app.extensions import db
from app.models import AIAnalysis, Listing, ListingImage


VALID = {
    "product_name": "Cordless Drill",
    "brand": "Acme",
    "model": "D100",
    "mpn": None,
    "gtin": None,
    "condition_suggestion": "Used",
    "condition_confidence": 0.82,
    "visible_observations": ["Scuff on battery base"],
    "visible_text": ["ACME", "D100"],
    "search_terms": ["Acme D100 drill", "cordless drill"],
    "detected_attributes": {"Color": "Black"},
    "uncertain_fields": ["mpn", "gtin"],
    "overall_confidence": 0.88,
}


class StubProvider(AIProvider):
    name = "stub"
    model = "stub-v1"

    def __init__(self, outputs):
        self.outputs = list(outputs)
        self.calls = []

    def analyze(self, images: list[AIImage], seller_notes: str | None) -> ProviderResult:
        self.calls.append({"images": images, "seller_notes": seller_notes})
        raw = json.dumps(self.outputs.pop(0))
        return ProviderResult(raw_json=raw, response_payload={"mock": True, "raw": raw})


@pytest.fixture
def stub_provider():
    return StubProvider([VALID])


def make_listing(app, *, seller_notes="Seller says brand is Acme", image_count=1):
    listing = Listing(sku="EBAY-AI-1", quantity=1, seller_notes=seller_notes)
    db.session.add(listing)
    db.session.flush()
    for index in range(image_count):
        filename = f"ai-{index}.jpg"
        path = app.config["UPLOAD_DIR"] / filename
        path.write_bytes(b"\xff\xd8\xff\xe0test")
        listing.images.append(ListingImage(filename=filename, original_filename=filename, mime_type="image/jpeg", size_bytes=path.stat().st_size, sort_order=index))
    db.session.commit()
    return listing


def test_valid_response_parsing():
    parsed = parse_analysis(json.dumps(VALID))
    assert parsed.brand == "Acme"
    assert parsed.overall_confidence == 0.88


def test_invalid_json_handling():
    with pytest.raises(AnalysisValidationError):
        parse_analysis("{not-json")


def test_null_and_uncertain_fields():
    parsed = parse_analysis(json.dumps(VALID))
    assert parsed.mpn is None
    assert parsed.gtin is None
    assert parsed.uncertain_fields == ["mpn", "gtin"]


def test_prompt_enforces_seller_note_precedence():
    prompt = build_user_prompt("Brand is SellerBrand")
    assert "Seller notes are authoritative" in SYSTEM_PROMPT
    assert "override conflicting visual guesses" in SYSTEM_PROMPT
    assert "Brand is SellerBrand" in prompt


def test_analysis_uses_all_images_notes_and_saves_raw_json(app, stub_provider):
    with app.app_context():
        listing = make_listing(app, image_count=2)
        result = analyze_listing(listing, provider=stub_provider)
        db.session.commit()
        assert result.product_name == "Cordless Drill"
        assert len(stub_provider.calls[0]["images"]) == 2
        assert stub_provider.calls[0]["seller_notes"] == "Seller says brand is Acme"
        assert listing.product_name == "Cordless Drill"
        assert listing.brand == "Acme"
        assert listing.ai_visible_text == ["ACME", "D100"]
        assert listing.ai_detected_attributes == {"Color": "Black"}
        record = db.session.query(AIAnalysis).one()
        assert json.loads(record.raw_json)["brand"] == "Acme"
        assert record.response_json["mock"] is True


def test_regenerate_preserves_user_edits_but_updates_untouched_ai_fields(app):
    provider = StubProvider([VALID, dict(VALID, brand="NewGuess", model="D200", search_terms=["new search"])])
    with app.app_context():
        listing = make_listing(app)
        analyze_listing(listing, provider=provider)
        db.session.commit()
        listing.brand = "Seller Corrected Brand"
        db.session.commit()
        analyze_listing(listing, provider=provider)
        db.session.commit()
        assert listing.brand == "Seller Corrected Brand"
        assert listing.model_number == "D200"
        assert listing.ai_search_terms == ["new search"]
        assert len(listing.ai_analyses) == 2


def test_explicit_replace_can_overwrite_user_edit(app):
    provider = StubProvider([VALID, dict(VALID, brand="Replacement")])
    with app.app_context():
        listing = make_listing(app)
        analyze_listing(listing, provider=provider)
        listing.brand = "Manual Brand"
        db.session.commit()
        analyze_listing(listing, provider=provider, replace_existing=True)
        db.session.commit()
        assert listing.brand == "Replacement"


def test_analyze_route_is_protected(client, app):
    with app.app_context():
        listing = make_listing(app)
        listing_id = listing.id
    response = client.post(f"/listings/{listing_id}/analyze")
    assert response.status_code == 302
    assert "/login" in response.headers["Location"]
