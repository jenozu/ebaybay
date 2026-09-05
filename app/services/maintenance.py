"""Recoverable local maintenance operations used by production runbooks."""
from __future__ import annotations

import sqlite3
from datetime import datetime, timedelta, timezone
from pathlib import Path

from ..models import ListingImage


def backup_sqlite_database(database_uri: str, backup_dir: Path, *, now=None) -> Path:
    prefix = "sqlite:///"
    if not database_uri.startswith(prefix):
        raise ValueError("Only SQLite database backups are supported by this application backup tool.")
    source_path = Path(database_uri[len(prefix):])
    if not source_path.is_file():
        raise FileNotFoundError("The configured database file is unavailable.")
    backup_dir.mkdir(parents=True, exist_ok=True)
    stamp = (now or datetime.now(timezone.utc)).strftime("%Y%m%dT%H%M%SZ")
    destination = backup_dir / f"ebaybay-{stamp}.db"
    with sqlite3.connect(source_path) as source, sqlite3.connect(destination) as target:
        source.backup(target)
    return destination


def restore_sqlite_database(backup_path: Path, database_uri: str) -> None:
    prefix = "sqlite:///"
    if not database_uri.startswith(prefix) or not backup_path.is_file() or backup_path.suffix != ".db":
        raise ValueError("Provide a valid SQLite backup file and SQLite database URI.")
    destination = Path(database_uri[len(prefix):])
    with sqlite3.connect(backup_path) as source, sqlite3.connect(destination) as target:
        source.backup(target)


def cleanup_unreferenced_uploads(upload_dir: Path, *, referenced_filenames: set[str], retention_days: int, apply: bool = False, now=None) -> list[Path]:
    """Return old unreferenced uploads; delete only with explicit apply=True."""
    cutoff = (now or datetime.now(timezone.utc)) - timedelta(days=max(0, retention_days))
    candidates = []
    if not upload_dir.is_dir():
        return candidates
    for path in upload_dir.iterdir():
        if not path.is_file() or path.name in referenced_filenames:
            continue
        modified = datetime.fromtimestamp(path.stat().st_mtime, timezone.utc)
        if modified < cutoff:
            candidates.append(path)
    if apply:
        for path in candidates:
            path.unlink(missing_ok=True)
    return candidates


def referenced_upload_names() -> set[str]:
    return {name for (name,) in ListingImage.query.with_entities(ListingImage.filename).all()}
