from pathlib import Path
from uuid import uuid4

from werkzeug.datastructures import FileStorage
from werkzeug.utils import secure_filename


class UploadValidationError(ValueError):
    pass


def _detected_mime(file: FileStorage) -> str | None:
    position = file.stream.tell()
    header = file.stream.read(16)
    file.stream.seek(position)
    if header.startswith(b"\xff\xd8\xff"):
        return "image/jpeg"
    if header.startswith(b"\x89PNG\r\n\x1a\n"):
        return "image/png"
    if len(header) >= 12 and header[:4] == b"RIFF" and header[8:12] == b"WEBP":
        return "image/webp"
    return None


def validate_image(file: FileStorage, allowed_extensions: set[str], allowed_mime_types: set[str]) -> str:
    original = secure_filename(file.filename or "")
    if not original or "." not in original:
        raise UploadValidationError("Image filename is missing or invalid.")

    ext = original.rsplit(".", 1)[1].lower()
    if ext not in allowed_extensions:
        raise UploadValidationError(f"Unsupported image extension: .{ext}")

    detected = _detected_mime(file)
    expected_for_ext = {"jpg": "image/jpeg", "jpeg": "image/jpeg", "png": "image/png", "webp": "image/webp"}.get(ext)
    if file.mimetype not in allowed_mime_types or detected not in allowed_mime_types or detected != expected_for_ext:
        raise UploadValidationError("File contents do not match a supported JPG, PNG, or WebP image.")
    return original


def save_image(file: FileStorage, upload_dir: Path, allowed_extensions: set[str], allowed_mime_types: set[str]) -> tuple[str, str, int]:
    original = validate_image(file, allowed_extensions, allowed_mime_types)
    ext = original.rsplit(".", 1)[1].lower()
    stored = f"{uuid4().hex}.{ext}"
    upload_dir.mkdir(parents=True, exist_ok=True)
    destination = upload_dir / stored
    file.save(destination)
    return stored, original, destination.stat().st_size
