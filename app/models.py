from datetime import datetime, timezone
from decimal import Decimal

from .extensions import db


class ListingStatus:
    DRAFT = "DRAFT"
    READY = "READY"
    STAGED = "STAGED"
    PUBLISHED = "PUBLISHED"
    FAILED = "FAILED"
    ARCHIVED = "ARCHIVED"
    ALL = {DRAFT, READY, STAGED, PUBLISHED, FAILED, ARCHIVED}
    TRANSITIONS = {DRAFT: {READY, ARCHIVED}, READY: {DRAFT, STAGED, ARCHIVED}, STAGED: {READY, PUBLISHED, FAILED}, FAILED: {DRAFT, READY, ARCHIVED}, PUBLISHED: set(), ARCHIVED: {DRAFT}}


def utcnow():
    return datetime.now(timezone.utc)


class Listing(db.Model):
    __tablename__ = "listings"
    id = db.Column(db.Integer, primary_key=True)
    sku = db.Column(db.String(64), nullable=False, unique=True, index=True)
    title = db.Column(db.String(255), nullable=True)
    product_name = db.Column(db.String(255), nullable=True)
    brand = db.Column(db.String(128), nullable=True)
    model_number = db.Column(db.String(128), nullable=True)
    mpn = db.Column(db.String(128), nullable=True)
    gtin = db.Column(db.String(64), nullable=True)
    seller_notes = db.Column(db.Text, nullable=True)
    condition = db.Column(db.String(64), nullable=True)
    quantity = db.Column(db.Integer, nullable=False, default=1)
    final_price = db.Column(db.Numeric(10, 2), nullable=True)
    status = db.Column(db.String(32), nullable=False, default=ListingStatus.DRAFT, index=True)
    ai_condition_suggestion = db.Column(db.String(64), nullable=True)
    ai_condition_confidence = db.Column(db.Float, nullable=True)
    ai_overall_confidence = db.Column(db.Float, nullable=True)
    ai_visible_observations = db.Column(db.JSON, nullable=False, default=list)
    ai_visible_text = db.Column(db.JSON, nullable=False, default=list)
    ai_search_terms = db.Column(db.JSON, nullable=False, default=list)
    ai_detected_attributes = db.Column(db.JSON, nullable=False, default=dict)
    ai_uncertain_fields = db.Column(db.JSON, nullable=False, default=list)
    ai_last_analyzed_at = db.Column(db.DateTime(timezone=True), nullable=True)
    ebay_category_id = db.Column(db.String(64), nullable=True)
    ebay_category_name = db.Column(db.String(255), nullable=True)
    ebay_category_path = db.Column(db.Text, nullable=True)
    ebay_category_candidates = db.Column(db.JSON, nullable=False, default=list)
    created_at = db.Column(db.DateTime(timezone=True), nullable=False, default=utcnow)
    updated_at = db.Column(db.DateTime(timezone=True), nullable=False, default=utcnow, onupdate=utcnow)
    images = db.relationship("ListingImage", back_populates="listing", cascade="all, delete-orphan", order_by="ListingImage.sort_order")
    aspects = db.relationship("ListingAspect", back_populates="listing", cascade="all, delete-orphan")
    comparables = db.relationship("ComparableListing", back_populates="listing", cascade="all, delete-orphan")
    ai_analyses = db.relationship("AIAnalysis", back_populates="listing", cascade="all, delete-orphan", order_by="AIAnalysis.created_at")

    def can_transition_to(self, new_status: str) -> bool:
        return new_status in ListingStatus.TRANSITIONS.get(self.status, set())

    def transition_to(self, new_status: str) -> None:
        if new_status not in ListingStatus.ALL:
            raise ValueError(f"Unknown listing status: {new_status}")
        if not self.can_transition_to(new_status):
            raise ValueError(f"Invalid listing transition: {self.status} -> {new_status}")
        self.status = new_status

    @property
    def price_display(self):
        if self.final_price is None:
            return None
        return f"{Decimal(self.final_price):.2f}"


class ListingImage(db.Model):
    __tablename__ = "listing_images"
    id = db.Column(db.Integer, primary_key=True)
    listing_id = db.Column(db.Integer, db.ForeignKey("listings.id", ondelete="CASCADE"), nullable=False, index=True)
    filename = db.Column(db.String(255), nullable=False)
    original_filename = db.Column(db.String(255), nullable=False)
    mime_type = db.Column(db.String(128), nullable=False)
    size_bytes = db.Column(db.Integer, nullable=False)
    sort_order = db.Column(db.Integer, nullable=False, default=0)
    created_at = db.Column(db.DateTime(timezone=True), nullable=False, default=utcnow)
    listing = db.relationship("Listing", back_populates="images")


class ListingAspect(db.Model):
    __tablename__ = "listing_aspects"
    id = db.Column(db.Integer, primary_key=True)
    listing_id = db.Column(db.Integer, db.ForeignKey("listings.id", ondelete="CASCADE"), nullable=False, index=True)
    name = db.Column(db.String(128), nullable=False)
    value = db.Column(db.String(255), nullable=True)
    required = db.Column(db.Boolean, nullable=False, default=False)
    recommended = db.Column(db.Boolean, nullable=False, default=False)
    listing = db.relationship("Listing", back_populates="aspects")


class ComparableListing(db.Model):
    __tablename__ = "comparable_listings"
    id = db.Column(db.Integer, primary_key=True)
    listing_id = db.Column(db.Integer, db.ForeignKey("listings.id", ondelete="CASCADE"), nullable=False, index=True)
    ebay_item_id = db.Column(db.String(64), nullable=True)
    title = db.Column(db.String(255), nullable=True)
    price = db.Column(db.Numeric(10, 2), nullable=True)
    currency = db.Column(db.String(8), nullable=True)
    url = db.Column(db.Text, nullable=True)
    similarity_score = db.Column(db.Float, nullable=True)
    listing = db.relationship("Listing", back_populates="comparables")


class AIAnalysis(db.Model):
    __tablename__ = "ai_analyses"
    id = db.Column(db.Integer, primary_key=True)
    listing_id = db.Column(db.Integer, db.ForeignKey("listings.id", ondelete="CASCADE"), nullable=False, index=True)
    provider = db.Column(db.String(64), nullable=False)
    model = db.Column(db.String(128), nullable=False)
    raw_json = db.Column(db.Text, nullable=False)
    response_json = db.Column(db.JSON, nullable=True)
    parsed_json = db.Column(db.JSON, nullable=False)
    created_at = db.Column(db.DateTime(timezone=True), nullable=False, default=utcnow)
    listing = db.relationship("Listing", back_populates="ai_analyses")


class EbayConnection(db.Model):
    __tablename__ = "ebay_connections"
    id = db.Column(db.Integer, primary_key=True)
    environment = db.Column(db.String(32), nullable=False, default="sandbox")
    marketplace_id = db.Column(db.String(32), nullable=False, default="EBAY_CA")
    account_label = db.Column(db.String(128), nullable=True)
    token_path = db.Column(db.String(255), nullable=False, default="/app/data/token.json")
    connected_at = db.Column(db.DateTime(timezone=True), nullable=True)
    updated_at = db.Column(db.DateTime(timezone=True), nullable=False, default=utcnow, onupdate=utcnow)
