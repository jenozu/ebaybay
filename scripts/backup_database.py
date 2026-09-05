"""Create a consistent SQLite database backup; safe to schedule from cron."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from app import create_app
from app.services.maintenance import backup_sqlite_database

app = create_app()
with app.app_context():
    path = backup_sqlite_database(app.config["SQLALCHEMY_DATABASE_URI"], app.config["BACKUP_DIR"])
    print(f"Created backup: {path.name}")
