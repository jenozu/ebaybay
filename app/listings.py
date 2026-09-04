from pathlib import Path

from flask import Blueprint, current_app, flash, redirect, render_template, send_from_directory, url_for
from sqlalchemy import select

from .auth import login_required
from .extensions import db
from .forms import ListingForm
from .models import Listing, ListingImage, ListingStatus
from .services.sku import generate_sku
from .services.uploads import UploadValidationError, save_image

bp = Blueprint("listings", __name__)


def _save_uploaded_images(listing: Listing, files) -> list[Path]:
    created_paths: list[Path] = []
    upload_dir = Path(current_app.config["UPLOAD_DIR"])
    valid_files = [f for f in files if f and f.filename]
    for index, file in enumerate(valid_files, start=len(listing.images)):
        stored, original, size = save_image(file, upload_dir, current_app.config["ALLOWED_IMAGE_EXTENSIONS"], current_app.config["ALLOWED_IMAGE_MIME_TYPES"])
        created_paths.append(upload_dir / stored)
        listing.images.append(ListingImage(filename=stored, original_filename=original, mime_type=file.mimetype, size_bytes=size, sort_order=index))
    return created_paths


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
        listing = Listing(sku=generate_sku(), title=form.title.data or None, condition=form.condition.data or None, quantity=form.quantity.data, seller_notes=form.seller_notes.data or None, status=ListingStatus.DRAFT)
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
    if form.validate_on_submit():
        created_paths: list[Path] = []
        try:
            listing.title = form.title.data or None
            listing.condition = form.condition.data or None
            listing.quantity = form.quantity.data
            listing.seller_notes = form.seller_notes.data or None
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
