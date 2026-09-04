import io

from app import create_app
from app.extensions import db
from app.models import Listing, ListingStatus


def test_create_draft_with_image(client, login, app):
    login()
    response = client.post("/listings/new", data={"title": "Test Widget", "condition": "Used", "quantity": "1", "seller_notes": "Visible wear on housing.", "images": (io.BytesIO(b"\xff\xd8\xff\xe0fakejpeg"), "widget.jpg")}, content_type="multipart/form-data", follow_redirects=True)
    assert response.status_code == 200
    assert b"Test Widget" in response.data
    with app.app_context():
        listing = db.session.query(Listing).one()
        assert listing.status == ListingStatus.DRAFT
        assert listing.sku.startswith("EBAY-")
        assert len(listing.images) == 1
        assert (app.config["UPLOAD_DIR"] / listing.images[0].filename).exists()


def test_rejects_invalid_image_mime(client, login, app):
    login()
    response = client.post("/listings/new", data={"quantity": "1", "images": (io.BytesIO(b"not-an-image"), "fake.jpg")}, content_type="multipart/form-data", follow_redirects=True)
    assert response.status_code == 200
    assert b"Unsupported image MIME type" in response.data
    with app.app_context():
        assert db.session.query(Listing).count() == 0


def test_edit_reopen_and_archive_restore(client, login, app):
    login()
    client.post("/listings/new", data={"quantity": "1", "seller_notes": "Original"}, follow_redirects=True)
    with app.app_context():
        listing_id = db.session.query(Listing.id).scalar()
    response = client.post(f"/listings/{listing_id}/edit", data={"title": "Edited title", "quantity": "2", "seller_notes": "Updated"}, follow_redirects=True)
    assert b"Edited title" in response.data
    assert b"Updated" in response.data
    client.post(f"/listings/{listing_id}/archive", follow_redirects=True)
    with app.app_context():
        assert db.session.get(Listing, listing_id).status == ListingStatus.ARCHIVED
    client.post(f"/listings/{listing_id}/restore", follow_redirects=True)
    with app.app_context():
        assert db.session.get(Listing, listing_id).status == ListingStatus.DRAFT


def test_draft_persists_across_app_instances(tmp_path):
    db_path = tmp_path / "persist.db"
    config = {"TESTING": True, "WTF_CSRF_ENABLED": False, "SESSION_COOKIE_SECURE": False, "SECRET_KEY": "x", "SQLALCHEMY_DATABASE_URI": f"sqlite:///{db_path}", "UPLOAD_DIR": tmp_path / "uploads"}
    first = create_app(config)
    with first.app_context():
        db.create_all()
        db.session.add(Listing(sku="EBAY-PERSIST-1", quantity=1, seller_notes="persistent"))
        db.session.commit()
        db.session.remove()
    second = create_app(config)
    with second.app_context():
        listing = db.session.query(Listing).filter_by(sku="EBAY-PERSIST-1").one()
        assert listing.seller_notes == "persistent"
