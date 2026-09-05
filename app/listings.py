from decimal import Decimal, InvalidOperation
from pathlib import Path

from flask import Blueprint, current_app, flash, redirect, render_template, request, send_from_directory, url_for
from sqlalchemy import select

from .ai.providers import AIConfigurationError, AIProviderError
from .ai.service import AnalysisValidationError, analyze_listing
from .auth import login_required
from .extensions import db
from .forms import ListingForm
from .models import ComparableListing, Listing, ListingImage, ListingStatus, utcnow
from .services.ebay.browse import BrowseClient, BrowseError, search_active_comparables
from .services.ebay.taxonomy import CategoryCandidate, TaxonomyClient, TaxonomyError, select_category, taxonomy_query
from .services.ebay.tokens import EbayTokenError
from .services.ebay.oauth import get_oauth_service
from .services.ebay.media import MediaServiceError, get_media_service
from .services.ebay.inventory import InventoryServiceError, get_inventory_service
from .services.ebay.offers import OfferServiceError, get_offer_service
from .services.pricing import calculate_pricing, strongest_comparables
from .services.writer import generate_condition_description, generate_description, generate_title
from .services.validation import validate_listing
from .services.sku import generate_sku
from .services.uploads import UploadValidationError, save_image

bp = Blueprint("listings", __name__)


def _validation_issues(listing: Listing):
    return validate_listing(
        listing, config=current_app.config, upload_dir=Path(current_app.config["UPLOAD_DIR"]),
        sku_exists=lambda sku, listing_id: db.session.scalar(select(Listing.id).where(Listing.sku == sku, Listing.id != listing_id)) is not None,
    )


def _invalidate_approval(listing: Listing) -> None:
    if listing.invalidate_approval():
        flash("Approval was cleared because this listing was changed. Review and approve it again.", "error")


def _taxonomy_client() -> TaxonomyClient:
    config = current_app.config
    return TaxonomyClient(
        environment=config["EBAY_ENVIRONMENT"],
        marketplace_id=config["EBAY_MARKETPLACE_ID"],
        api_base=config["EBAY_API_BASE"],
        timeout=config["EBAY_HTTP_TIMEOUT_SECONDS"],
        access_token_provider=lambda: get_oauth_service().get_access_token(),
    )


def _browse_client() -> BrowseClient:
    config = current_app.config
    return BrowseClient(
        environment=config["EBAY_ENVIRONMENT"], marketplace_id=config["EBAY_MARKETPLACE_ID"],
        api_base=config["EBAY_API_BASE"], timeout=config["EBAY_HTTP_TIMEOUT_SECONDS"],
        access_token_provider=lambda: get_oauth_service().get_access_token(),
    )


def _save_uploaded_images(listing: Listing, files) -> list[Path]:
    created_paths: list[Path] = []
    upload_dir = Path(current_app.config["UPLOAD_DIR"])
    valid_files = [f for f in files if f and f.filename]
    for index, file in enumerate(valid_files, start=len(listing.images)):
        stored, original, size = save_image(file, upload_dir, current_app.config["ALLOWED_IMAGE_EXTENSIONS"], current_app.config["ALLOWED_IMAGE_MIME_TYPES"])
        created_paths.append(upload_dir / stored)
        listing.images.append(ListingImage(filename=stored, original_filename=original, mime_type=file.mimetype, size_bytes=size, sort_order=index))
    return created_paths


def _split_lines(value: str | None) -> list[str]:
    return [line.strip() for line in (value or "").splitlines() if line.strip()]


def _parse_attributes(value: str | None) -> dict[str, str]:
    attributes: dict[str, str] = {}
    for line in _split_lines(value):
        if ":" in line:
            key, item_value = line.split(":", 1)
            key = key.strip()
            if key:
                attributes[key] = item_value.strip()
    return attributes


def _format_attributes(attributes: dict | None) -> str:
    return "\n".join(f"{key}: {value}" for key, value in (attributes or {}).items())


def _apply_form(listing: Listing, form: ListingForm) -> None:
    original_title = form.original_title.data or None
    if listing.id is None or (form.title.data or None) != original_title:
        listing.title_manual = bool(form.title.data)
    listing.title = form.title.data or None
    listing.product_name = form.product_name.data or None
    listing.brand = form.brand.data or None
    listing.model_number = form.model_number.data or None
    listing.mpn = form.mpn.data or None
    listing.gtin = form.gtin.data or None
    listing.condition = form.condition.data or None
    listing.quantity = form.quantity.data
    original = None
    try:
        original = Decimal(form.original_final_price.data) if form.original_final_price.data else None
    except InvalidOperation:
        pass
    if listing.id is None or form.final_price.data != original:
        listing.final_price_manual = form.final_price.data is not None
    listing.final_price = form.final_price.data
    listing.seller_notes = form.seller_notes.data or None
    listing.ai_visible_text = _split_lines(form.visible_text_text.data)
    listing.ai_search_terms = _split_lines(form.search_terms_text.data)
    listing.ai_detected_attributes = _parse_attributes(form.attributes_text.data)


def _prepare_edit_form(form: ListingForm, listing: Listing) -> None:
    if not form.is_submitted():
        form.visible_text_text.data = "\n".join(listing.ai_visible_text or [])
        form.search_terms_text.data = "\n".join(listing.ai_search_terms or [])
        form.attributes_text.data = _format_attributes(listing.ai_detected_attributes)
        form.original_final_price.data = listing.price_display or ""
        form.original_title.data = listing.title or ""


@bp.get("/dashboard")
@login_required
def dashboard():
    listings = db.session.scalars(select(Listing).order_by(Listing.updated_at.desc())).all()
    return render_template("dashboard.html", listings=listings)


@bp.route("/listings/new", methods=["GET", "POST"])
@login_required
def new_listing():
    form = ListingForm()
    if form.validate_on_submit():
        listing = Listing(sku=generate_sku(), status=ListingStatus.DRAFT)
        _apply_form(listing, form)
        created_paths: list[Path] = []
        try:
            db.session.add(listing)
            created_paths = _save_uploaded_images(listing, form.images.data or [])
            db.session.commit()
        except UploadValidationError as exc:
            db.session.rollback()
            for path in created_paths:
                path.unlink(missing_ok=True)
            flash(str(exc), "error")
            return render_template("listing_form.html", form=form, listing=None)
        except Exception:
            db.session.rollback()
            for path in created_paths:
                path.unlink(missing_ok=True)
            raise
        flash("Draft created.", "success")
        return redirect(url_for("listings.detail", listing_id=listing.id))
    return render_template("listing_form.html", form=form, listing=None)


@bp.get("/listings/<int:listing_id>")
@login_required
def detail(listing_id):
    listing = db.get_or_404(Listing, listing_id)
    return render_template("listing_detail.html", listing=listing, validation_issues=_validation_issues(listing))


@bp.route("/listings/<int:listing_id>/edit", methods=["GET", "POST"])
@login_required
def edit(listing_id):
    listing = db.get_or_404(Listing, listing_id)
    form = ListingForm(obj=listing)
    _prepare_edit_form(form, listing)
    if form.validate_on_submit():
        created_paths: list[Path] = []
        try:
            _invalidate_approval(listing)
            _apply_form(listing, form)
            created_paths = _save_uploaded_images(listing, form.images.data or [])
            db.session.commit()
        except UploadValidationError as exc:
            db.session.rollback()
            for path in created_paths:
                path.unlink(missing_ok=True)
            flash(str(exc), "error")
            return render_template("listing_form.html", form=form, listing=listing)
        except Exception:
            db.session.rollback()
            for path in created_paths:
                path.unlink(missing_ok=True)
            raise
        flash("Draft updated.", "success")
        return redirect(url_for("listings.detail", listing_id=listing.id))
    return render_template("listing_form.html", form=form, listing=listing)


@bp.post("/listings/<int:listing_id>/analyze")
@login_required
def analyze(listing_id):
    listing = db.get_or_404(Listing, listing_id)
    if listing.status == ListingStatus.READY:
        flash("Return an approved listing to DRAFT before running AI analysis.", "error")
        return redirect(url_for("listings.detail", listing_id=listing.id))
    replace_existing = request.form.get("replace_existing") == "1"
    try:
        _invalidate_approval(listing)
        analyze_listing(listing, replace_existing=replace_existing)
        db.session.commit()
    except (AIConfigurationError, AIProviderError, AnalysisValidationError) as exc:
        db.session.rollback()
        flash(str(exc), "error")
    else:
        flash("AI product analysis complete.", "success")
    return redirect(url_for("listings.detail", listing_id=listing.id))


@bp.post("/listings/<int:listing_id>/taxonomy/suggest")
@login_required
def suggest_taxonomy(listing_id):
    listing = db.get_or_404(Listing, listing_id)
    query = taxonomy_query(listing)
    if not query:
        flash("Add a product name, title, or search terms before requesting categories.", "error")
        return redirect(url_for("listings.detail", listing_id=listing.id))
    try:
        _invalidate_approval(listing)
        client = _taxonomy_client()
        candidates = client.suggest_categories(query)
        listing.ebay_category_candidates = [candidate.as_dict() for candidate in candidates]
        if candidates and not listing.ebay_category_id:
            select_category(listing, client, candidates[0])
        db.session.commit()
    except (EbayTokenError, TaxonomyError) as exc:
        db.session.rollback()
        flash(str(exc), "error")
    else:
        flash("eBay category suggestions updated." if candidates else "eBay returned no category suggestions.", "success")
    return redirect(url_for("listings.detail", listing_id=listing.id))


@bp.post("/listings/<int:listing_id>/taxonomy/category")
@login_required
def update_category(listing_id):
    listing = db.get_or_404(Listing, listing_id)
    category_id = (request.form.get("category_id") or "").strip()
    category_name = (request.form.get("category_name") or "").strip()
    category_path = (request.form.get("category_path") or "").strip()
    if not category_id or not category_name:
        flash("Category ID and category name are required.", "error")
        return redirect(url_for("listings.detail", listing_id=listing.id))
    try:
        _invalidate_approval(listing)
        select_category(listing, _taxonomy_client(), CategoryCandidate(category_id, category_name, category_path or category_name))
        db.session.commit()
    except (EbayTokenError, TaxonomyError) as exc:
        db.session.rollback()
        flash(str(exc), "error")
    else:
        flash("eBay category and official item specifics updated.", "success")
    return redirect(url_for("listings.detail", listing_id=listing.id))


@bp.post("/listings/<int:listing_id>/taxonomy/aspects")
@login_required
def update_aspects(listing_id):
    listing = db.get_or_404(Listing, listing_id)
    _invalidate_approval(listing)
    for aspect in listing.aspects:
        aspect.value = (request.form.get(f"aspect_{aspect.id}") or "").strip() or None
    db.session.commit()
    flash("Item specifics saved.", "success")
    return redirect(url_for("listings.detail", listing_id=listing.id))


@bp.post("/listings/<int:listing_id>/comparables/refresh")
@login_required
def refresh_comparables(listing_id):
    listing = db.get_or_404(Listing, listing_id)
    try:
        _invalidate_approval(listing)
        currency = current_app.config["EBAY_CURRENCY"]
        items = search_active_comparables(listing, _browse_client(), relevance_filter=lambda found: strongest_comparables(listing, found, currency=currency))
        scored = strongest_comparables(listing, items, currency=currency)
        listing.comparables = [ComparableListing(
            ebay_item_id=entry.item.item_id, title=entry.item.title, price=entry.item.price,
            shipping_cost=entry.item.shipping_cost, total_price=entry.item.total_price,
            currency=entry.item.currency, url=entry.item.url, condition=entry.item.condition,
            category_id=entry.item.category_id, search_query=entry.item.search_query,
            similarity_score=entry.score,
        ) for entry in scored]
        summary = calculate_pricing(scored)
        fields = ("comparable_low", "comparable_high", "comparable_median", "quick_sale_price", "recommended_price", "high_target_price", "pricing_confidence", "pricing_explanation")
        if summary:
            values = (summary.low, summary.high, summary.median, summary.quick_sale, summary.recommended, summary.high_target, summary.confidence, summary.explanation)
            for field, value in zip(fields, values):
                setattr(listing, field, value)
            if not listing.final_price_manual:
                listing.final_price = summary.recommended
        else:
            for field in fields:
                setattr(listing, field, None)
            if not listing.final_price_manual:
                listing.final_price = None
        listing.comparables_last_searched_at = utcnow()
        db.session.commit()
    except (EbayTokenError, BrowseError) as exc:
        db.session.rollback()
        flash(str(exc), "error")
    else:
        flash(f"Active comparables updated: {len(scored)} relevant listings retained.", "success")
    return redirect(url_for("listings.detail", listing_id=listing.id))


@bp.post("/listings/<int:listing_id>/images/upload")
@login_required
def upload_images_to_ebay(listing_id):
    listing = db.get_or_404(Listing, listing_id)
    try:
        uploaded, skipped = get_media_service().upload_listing_images(listing, Path(current_app.config["UPLOAD_DIR"]))
    except (EbayTokenError, MediaServiceError) as exc:
        flash(str(exc), "error")
    else:
        flash(f"eBay image upload complete: {uploaded} uploaded, {skipped} already current.", "success")
    return redirect(url_for("listings.detail", listing_id=listing.id))


@bp.post("/listings/<int:listing_id>/inventory/stage")
@login_required
def stage_inventory_item(listing_id):
    listing = db.get_or_404(Listing, listing_id)
    try:
        changed = get_inventory_service().stage(listing)
    except (EbayTokenError, InventoryServiceError) as exc:
        flash(str(exc), "error")
    else:
        flash("eBay Inventory Item staged (not live)." if changed else "eBay Inventory Item is already current (not live).", "success")
    return redirect(url_for("listings.detail", listing_id=listing.id))


@bp.post("/listings/<int:listing_id>/offer/stage")
@login_required
def stage_offer(listing_id):
    listing = db.get_or_404(Listing, listing_id)
    try:
        changed = get_offer_service().stage(listing)
    except (EbayTokenError, OfferServiceError) as exc:
        flash(str(exc), "error")
    else:
        flash("Unpublished eBay offer staged. It is not live." if changed else "Unpublished eBay offer is already current. It is not live.", "success")
    return redirect(url_for("listings.detail", listing_id=listing.id))


def _regenerate_field(listing: Listing, field: str, replace_manual: bool) -> bool:
    manual_field = f"{field}_manual"
    if getattr(listing, field) and getattr(listing, manual_field) and not replace_manual:
        return False
    writers = {
        "title": lambda: generate_title(listing, current_app.config["EBAY_TITLE_MAX_LENGTH"]),
        "description": lambda: generate_description(listing),
        "condition_description": lambda: generate_condition_description(listing),
    }
    setattr(listing, field, writers[field]())
    setattr(listing, manual_field, False)
    listing.copy_generated_at = utcnow()
    return True


@bp.post("/listings/<int:listing_id>/copy/regenerate/<field>")
@login_required
def regenerate_copy(listing_id, field):
    if field not in {"title", "description", "condition_description"}:
        return "Unknown copy field", 404
    listing = db.get_or_404(Listing, listing_id)
    _invalidate_approval(listing)
    changed = _regenerate_field(listing, field, request.form.get("replace_manual") == "1")
    if changed:
        db.session.commit()
        flash(f"Generated {field.replace('_', ' ')} saved. It remains editable.", "success")
    else:
        flash(f"Manual {field.replace('_', ' ')} was preserved. Select replace to overwrite it.", "error")
    return redirect(url_for("listings.detail", listing_id=listing.id))


@bp.post("/listings/<int:listing_id>/copy/save")
@login_required
def save_copy(listing_id):
    listing = db.get_or_404(Listing, listing_id)
    _invalidate_approval(listing)
    for field in ("title", "description", "condition_description"):
        value = (request.form.get(field) or "").strip() or None
        if field == "title" and value and len(value) > current_app.config["EBAY_TITLE_MAX_LENGTH"]:
            flash(f"Title must be {current_app.config['EBAY_TITLE_MAX_LENGTH']} characters or fewer.", "error")
            return redirect(url_for("listings.detail", listing_id=listing.id))
        original = (request.form.get(f"original_{field}") or "").strip() or None
        if value != original:
            setattr(listing, field, value)
            setattr(listing, f"{field}_manual", value is not None)
    db.session.commit()
    flash("Listing copy saved.", "success")
    return redirect(url_for("listings.detail", listing_id=listing.id))


@bp.post("/listings/<int:listing_id>/validate")
@login_required
def validate_draft(listing_id):
    listing = db.get_or_404(Listing, listing_id)
    issues = _validation_issues(listing)
    flash("Validation passed; approval is still required." if not issues else f"Validation found {len(issues)} blocking issue(s).", "success" if not issues else "error")
    return redirect(url_for("listings.detail", listing_id=listing.id))


@bp.post("/listings/<int:listing_id>/approve")
@login_required
def approve_listing(listing_id):
    listing = db.get_or_404(Listing, listing_id)
    issues = _validation_issues(listing)
    if issues:
        flash("Listing cannot be approved until every validation error is resolved.", "error")
    elif listing.status == ListingStatus.DRAFT:
        listing.transition_to(ListingStatus.READY)
        db.session.commit()
        flash("Listing approved and marked READY.", "success")
    elif listing.status == ListingStatus.READY:
        flash("Listing is already approved and READY.", "success")
    else:
        flash(f"Listing in {listing.status} cannot be approved.", "error")
    return redirect(url_for("listings.detail", listing_id=listing.id))


@bp.post("/listings/<int:listing_id>/return-to-draft")
@login_required
def return_to_draft(listing_id):
    listing = db.get_or_404(Listing, listing_id)
    if listing.status == ListingStatus.READY:
        listing.transition_to(ListingStatus.DRAFT)
        db.session.commit()
        flash("Listing returned to DRAFT.", "success")
    else:
        flash("Only an approved READY listing can be returned to draft.", "error")
    return redirect(url_for("listings.detail", listing_id=listing.id))


@bp.post("/listings/<int:listing_id>/archive")
@login_required
def archive(listing_id):
    listing = db.get_or_404(Listing, listing_id)
    if listing.status != ListingStatus.ARCHIVED:
        listing.transition_to(ListingStatus.ARCHIVED)
        db.session.commit()
    flash("Draft archived.", "success")
    return redirect(url_for("listings.dashboard"))


@bp.post("/listings/<int:listing_id>/restore")
@login_required
def restore(listing_id):
    listing = db.get_or_404(Listing, listing_id)
    if listing.status == ListingStatus.ARCHIVED:
        listing.transition_to(ListingStatus.DRAFT)
        db.session.commit()
    flash("Draft restored.", "success")
    return redirect(url_for("listings.detail", listing_id=listing.id))


@bp.post("/listings/<int:listing_id>/delete")
@login_required
def delete(listing_id):
    listing = db.get_or_404(Listing, listing_id)
    if listing.status not in {ListingStatus.DRAFT, ListingStatus.ARCHIVED}:
        flash("Only draft or archived listings can be deleted.", "error")
        return redirect(url_for("listings.detail", listing_id=listing.id))
    upload_dir = Path(current_app.config["UPLOAD_DIR"])
    filenames = [image.filename for image in listing.images]
    db.session.delete(listing)
    db.session.commit()
    for filename in filenames:
        (upload_dir / filename).unlink(missing_ok=True)
    flash("Draft deleted.", "success")
    return redirect(url_for("listings.dashboard"))


@bp.get("/uploads/<path:filename>")
@login_required
def uploaded_file(filename):
    return send_from_directory(current_app.config["UPLOAD_DIR"], filename)
