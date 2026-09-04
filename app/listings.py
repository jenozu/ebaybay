from pathlib import Path

from flask import Blueprint, current_app, flash, redirect, render_template, request, send_from_directory, url_for
from sqlalchemy import select

from .ai.providers import AIConfigurationError, AIProviderError
from .ai.service import AnalysisValidationError, analyze_listing
from .auth import login_required
from .extensions import db
from .forms import ListingForm
from .models import Listing, ListingImage, ListingStatus
from .services.ebay.taxonomy import CategoryCandidate, TaxonomyClient, TaxonomyError, select_category, taxonomy_query
from .services.ebay.tokens import EbayTokenError, load_access_token
from .services.sku import generate_sku
from .services.uploads import UploadValidationError, save_image

bp = Blueprint("listings", __name__)


def _taxonomy_client() -> TaxonomyClient:
    config = current_app.config
    return TaxonomyClient(
        environment=config["EBAY_ENVIRONMENT"],
        marketplace_id=config["EBAY_MARKETPLACE_ID"],
        api_base=config["EBAY_API_BASE"],
        timeout=config["EBAY_HTTP_TIMEOUT_SECONDS"],
        access_token_provider=lambda: load_access_token(config["EBAY_TOKEN_PATH"]),
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
    listing.title = form.title.data or None
    listing.product_name = form.product_name.data or None
    listing.brand = form.brand.data or None
    listing.model_number = form.model_number.data or None
    listing.mpn = form.mpn.data or None
    listing.gtin = form.gtin.data or None
    listing.condition = form.condition.data or None
    listing.quantity = form.quantity.data
    listing.seller_notes = form.seller_notes.data or None
    listing.ai_visible_text = _split_lines(form.visible_text_text.data)
    listing.ai_search_terms = _split_lines(form.search_terms_text.data)
    listing.ai_detected_attributes = _parse_attributes(form.attributes_text.data)


def _prepare_edit_form(form: ListingForm, listing: Listing) -> None:
    if not form.is_submitted():
        form.visible_text_text.data = "\n".join(listing.ai_visible_text or [])
        form.search_terms_text.data = "\n".join(listing.ai_search_terms or [])
        form.attributes_text.data = _format_attributes(listing.ai_detected_attributes)


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
    return render_template("listing_detail.html", listing=listing)


@bp.route("/listings/<int:listing_id>/edit", methods=["GET", "POST"])
@login_required
def edit(listing_id):
    listing = db.get_or_404(Listing, listing_id)
    form = ListingForm(obj=listing)
    _prepare_edit_form(form, listing)
    if form.validate_on_submit():
        created_paths: list[Path] = []
        try:
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
    replace_existing = request.form.get("replace_existing") == "1"
    try:
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
    for aspect in listing.aspects:
        aspect.value = (request.form.get(f"aspect_{aspect.id}") or "").strip() or None
    db.session.commit()
    flash("Item specifics saved.", "success")
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
