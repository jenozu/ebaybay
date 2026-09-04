from pydantic import BaseModel, ConfigDict, Field


class ProductAnalysis(BaseModel):
    model_config = ConfigDict(extra="forbid")

    product_name: str | None = None
    brand: str | None = None
    model: str | None = None
    mpn: str | None = None
    gtin: str | None = None
    condition_suggestion: str | None = None
    condition_confidence: float | None = Field(default=None, ge=0, le=1)
    visible_observations: list[str] = Field(default_factory=list)
    visible_text: list[str] = Field(default_factory=list)
    search_terms: list[str] = Field(default_factory=list)
    detected_attributes: dict[str, str] = Field(default_factory=dict)
    uncertain_fields: list[str] = Field(default_factory=list)
    overall_confidence: float | None = Field(default=None, ge=0, le=1)
