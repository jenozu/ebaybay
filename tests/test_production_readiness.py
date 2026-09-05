import logging
import os
import time
from datetime import datetime, timedelta, timezone
from pathlib import Path

import pytest

from app import create_app
from app.config import SecretRedactingFilter
from app.extensions import db
from app.models import Listing, ListingImage
from app.services.maintenance import backup_sqlite_database, cleanup_unreferenced_uploads, restore_sqlite_database


def production_config(tmp_path):
    return {"TESTING": True, "EBAY_ENVIRONMENT": "production", "EBAY_MARKETPLACE_ID": "EBAY_CA", "SECRET_KEY": "not-default", "APP_PASSWORD_HASH": "hash", "SESSION_COOKIE_SECURE": True, "EBAY_CLIENT_ID": "id", "EBAY_CLIENT_SECRET": "secret", "EBAY_RUNAME": "runame", "EBAY_TOKEN_ENCRYPTION_KEY": "OUQxY9tKooYQgtzMO1FCPaOeT8VGdrz7BpwVeODDcQY=", "SQLALCHEMY_DATABASE_URI": f"sqlite:///{tmp_path / 'prod.db'}", "UPLOAD_DIR": tmp_path / "uploads", "BACKUP_DIR": tmp_path / "backups"}


def test_production_configuration_fails_closed_for_unsafe_values(tmp_path):
    config = production_config(tmp_path); config["SECRET_KEY"] = "change-me-before-production"
    with pytest.raises(RuntimeError, match="SECRET_KEY"):
        create_app(config)
    config = production_config(tmp_path); config["EBAY_MARKETPLACE_ID"] = "EBAY_US"
    with pytest.raises(RuntimeError, match="EBAY_CA"):
        create_app(config)
    assert create_app(production_config(tmp_path)).config["EBAY_ENVIRONMENT"] == "production"


def test_structured_logging_filter_redacts_sensitive_payloads():
    record = logging.LogRecord("test", logging.INFO, __file__, 1, "access_token=should-not-appear", (), None)
    assert SecretRedactingFilter().filter(record) is True
    assert record.getMessage() == "Sensitive eBay credential data redacted."


def test_container_uses_gunicorn_with_structured_stream_logs():
    entrypoint = (Path(__file__).resolve().parents[1] / "docker-entrypoint.sh").read_text()
    assert "gunicorn" in entrypoint and "--access-logfile -" in entrypoint and "--capture-output" in entrypoint


def test_sqlite_backup_and_restore_are_reproducible(app, tmp_path):
    with app.app_context():
        db.session.add(Listing(sku="BACKUP-1", quantity=1)); db.session.commit()
        backup = backup_sqlite_database(app.config["SQLALCHEMY_DATABASE_URI"], tmp_path / "backups", now=datetime(2026, 1, 1, tzinfo=timezone.utc))
        db.session.add(Listing(sku="AFTER-BACKUP", quantity=1)); db.session.commit()
        restore_sqlite_database(backup, app.config["SQLALCHEMY_DATABASE_URI"])
        db.session.remove()
        assert db.session.query(Listing).filter_by(sku="BACKUP-1").one()
        assert db.session.query(Listing).filter_by(sku="AFTER-BACKUP").one_or_none() is None


def test_upload_cleanup_keeps_referenced_files_and_requires_explicit_apply(app):
    with app.app_context():
        referenced = app.config["UPLOAD_DIR"] / "referenced.jpg"; stale = app.config["UPLOAD_DIR"] / "stale.jpg"; referenced.write_bytes(b"x"); stale.write_bytes(b"x")
        old = time.time() - 40 * 86400; os.utime(referenced, (old, old)); os.utime(stale, (old, old))
        listing = Listing(sku="CLEANUP-1", quantity=1); listing.images.append(ListingImage(filename="referenced.jpg", original_filename="referenced.jpg", mime_type="image/jpeg", size_bytes=1)); db.session.add(listing); db.session.commit()
        candidates = cleanup_unreferenced_uploads(app.config["UPLOAD_DIR"], referenced_filenames={"referenced.jpg"}, retention_days=30)
        assert candidates == [stale] and stale.exists()
        cleanup_unreferenced_uploads(app.config["UPLOAD_DIR"], referenced_filenames={"referenced.jpg"}, retention_days=30, apply=True)
        assert not stale.exists() and referenced.exists()
