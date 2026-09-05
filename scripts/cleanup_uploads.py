"""Preview old unreferenced uploads; pass --apply for the irreversible deletion."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app import create_app
from app.services.maintenance import cleanup_unreferenced_uploads, referenced_upload_names

apply = "--apply" in sys.argv
app = create_app()
with app.app_context():
    paths = cleanup_unreferenced_uploads(app.config["UPLOAD_DIR"], referenced_filenames=referenced_upload_names(), retention_days=app.config["UPLOAD_RETENTION_DAYS"], apply=apply)
    print(f"{'Deleted' if apply else 'Would delete'} {len(paths)} unreferenced upload(s).")
