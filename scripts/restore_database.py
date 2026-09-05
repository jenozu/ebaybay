"""Restore a SQLite backup only when a deliberate confirmation flag is supplied."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app import create_app
from app.services.maintenance import restore_sqlite_database

if len(sys.argv) != 3 or sys.argv[1] != "--confirm-restore":
    raise SystemExit("Usage: python scripts/restore_database.py --confirm-restore /path/to/backup.db")
app = create_app()
with app.app_context():
    restore_sqlite_database(Path(sys.argv[2]), app.config["SQLALCHEMY_DATABASE_URI"])
    print("Database restore completed.")
