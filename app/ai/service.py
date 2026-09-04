from pathlib import Path

from flask import current_app
from pydantic import ValidationError

from ..models import AIAnalysis, Listing, utcnow
from .providers import AIImage, AIProvider, get_ai_provider
from .schema import ProductAnalysis


class AnalysisValidationError(ValueError):
    pass


def parse_analysis(raw_json: str) -> ProductAnalysis:
    try:
        return ProductAnalysis.model_validate_json(raw_json)
    except ValidationError as exc:
        raise AnalysisValidationError(f"AI output failed schema validation: {exc}") from exc


def analyze_listing(listing: Listing, provider: AIProvider | None = None, replace_existing: bool = False) -> ProductAnalysis:
    if not listing.images:
        raise AnalysisValidationError("Add at least one product photo before running AI analysis.")

    upload_dir = Path(current_app.config["UPLOAD_DIR"])
    images: list[AIImage] = []
    for image in listing.images:
        path = upload_dir / image.filename
        if not path.is_file():
            raise AnalysisValidationError(f"Stored image is missing: {image.filename}")
        images.append(AIImage(path=path, mime_type=image.mime_type))

    provider = provider or get_ai_provider()
    result = provider.analyze(images, listing.seller_notes)
    analysis = parse_analysis(result.raw_json)
    previous = listing.ai_analyses[-1].parsed_json if listing.ai_analyses else None
    _apply_analysis(listing, analysis, previous or {}, replace_existing)

    listing.ai_analyses.append(
        AIAnalysis(
            provider=provider.name,
            model=provider.model,
            raw_json=result.raw_json,
            response_json=result.response_payload,
            parsed_json=analysis.model_dump(mode="json"),
        )
    )
    listing.ai_last_analyzed_at = utcnow()
    return analysis


def _apply_analysis(listing: Listing, analysis: ProductAnalysis, previous: dict, replace_existing: bool) -> None:
    direct_fields = {
        "product_name": "product_name",
        "brand": "brand",
        "model_number": "model",
        "mpn": "mpn",
        "gtin": "gtin",
        "condition": "condition_suggestion",
    }
    values = analysis.model_dump(mode="json")
    for listing_field, analysis_field in direct_fields.items():
        new_value = values.get(analysis_field)
        current_value = getattr(listing, listing_field)
        previous_value = previous.get(analysis_field)
        if replace_existing or current_value in (None, "") or current_value == previous_value:
            setattr(listing, listing_field, new_value)

    collection_fields = {
        "ai_visible_text": "visible_text",
        "ai_search_terms": "search_terms",
        "ai_detected_attributes": "detected_attributes",
    }
    for listing_field, analysis_field in collection_fields.items():
        current_value = getattr(listing, listing_field) or ([] if analysis_field != "detected_attributes" else {})
        previous_value = previous.get(analysis_field)
        new_value = values.get(analysis_field)
        if replace_existing or not current_value or current_value == previous_value:
            setattr(listing, listing_field, new_value)

    listing.ai_condition_suggestion = analysis.condition_suggestion
    listing.ai_condition_confidence = analysis.condition_confidence
    listing.ai_overall_confidence = analysis.overall_confidence
    listing.ai_visible_observations = analysis.visible_observations
    listing.ai_uncertain_fields = analysis.uncertain_fields
