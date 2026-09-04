from pathlib import Path
from uuid import uuid4

from werkzeug.datastructures import FileStorage
from werkzeug.utils import secure_filename


class UploadValidationError(ValueError):
    pass


def validate_image(file: FileStorage, allowed_extensions: set[str], allowed_mime_types: set[str]) -> str:
    original = secure_filename(file.filename or "")
    if not original or "." not in original:
        raise UploadValidationError("Image filename is missing or invalid.")
    ext = original.rsplit(".", 1)[1].lower()
    if ext not in allowed_extensions:
        raise UploadValidationError(f"Unsupported image extension: .{ext}")
    if file.mimetype not in allowed_mime_types:
        raise UploadValidationError(f"Unsupported image MIME type: {file.mimetype or 'unknown'}")
    return original


def save_image(file: FileStorage, upload_dir: Path, allowed_extensions: set[str], allowed_mime_types: set[str]) -> tuple[str, str, int]:
    original = validate_image(file, allowed_extensions, allowed_mime_types)
    ext = original.rsplit(".", 1)[1].lower()
    stored = f"{uuid4().hex}.{ext}"
    upload_dir.mkdir(parents=True, exist_ok=True)
    destination = upload_dir / stored
    file.save(destination)
    return stored, original, destination.stat().st_size
