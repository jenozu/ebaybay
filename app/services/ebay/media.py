"""eBay Media API image upload with local persistence and bounded retries."""
from __future__ import annotations

import hashlib
import time
from pathlib import Path

import requests

from ...extensions import db
from ...models import Listing, ListingImage, ListingStatus, utcnow
from .oauth import OAuthError, get_oauth_service


class MediaServiceError(OAuthError):
    """Safe Media API error; it never includes API response or token content."""


class MediaService:
    def __init__(self, config: dict, *, http=None, token_provider=None, sleeper=None):
        self.config = config
        self.http = http or requests
        self.token_provider = token_provider or (lambda: get_oauth_service(config).get_access_token())
        self.sleeper = sleeper or time.sleep

    @property
    def base_url(self) -> str:
        configured = self.config.get("EBAY_API_BASE")
        if configured:
            return configured.rstrip("/")
        return "https://api.sandbox.ebay.com" if self.config["EBAY_ENVIRONMENT"].lower() == "sandbox" else "https://api.ebay.com"

    @property
    def endpoint(self) -> str:
        return f"{self.base_url}/sell/media/v1/image/create_image_from_file"

    def upload_image(self, image: ListingImage, path: Path) -> bool:
        if not path.is_file():
            image.ebay_upload_status = "FAILED"
            image.ebay_upload_error = "Local image file is unavailable."
            db.session.commit()
            raise MediaServiceError("A local listing image is unavailable.")
        content = path.read_bytes()
        fingerprint = hashlib.sha256(content).hexdigest()
        if image.ebay_image_id and image.ebay_image_url and image.ebay_upload_fingerprint == fingerprint:
            image.ebay_upload_status = "UPLOADED"
            image.ebay_upload_error = None
            db.session.commit()
            return False
        image.ebay_upload_status = "UPLOADING"
        image.ebay_upload_error = None
        db.session.commit()
        retries = max(1, int(self.config.get("EBAY_MEDIA_MAX_RETRIES", 3)))
        last_error = "eBay image upload failed."
        for attempt in range(retries):
            try:
                response = self.http.post(self.endpoint, headers={"Authorization": f"Bearer {self.token_provider()}", "Content-Type": image.mime_type, "Accept": "application/json"}, data=content, timeout=self.config["EBAY_HTTP_TIMEOUT_SECONDS"])
            except requests.RequestException:
                transient = True
            else:
                transient = getattr(response, "status_code", 0) == 429 or 500 <= getattr(response, "status_code", 0) < 600
                try:
                    payload = response.json()
                except (ValueError, TypeError):
                    payload = None
                if getattr(response, "ok", False) and isinstance(payload, dict):
                    image_id, image_url = payload.get("imageId"), payload.get("imageUrl")
                    if isinstance(image_id, str) and image_id and isinstance(image_url, str) and image_url:
                        image.ebay_image_id = image_id
                        image.ebay_image_url = image_url
                        image.ebay_upload_fingerprint = fingerprint
                        image.ebay_upload_status = "UPLOADED"
                        image.ebay_upload_error = None
                        image.ebay_uploaded_at = utcnow()
                        db.session.commit()
                        return True
                    transient = False
                    last_error = "eBay returned an invalid image-upload response."
                elif not transient:
                    last_error = "eBay rejected the image upload. Check the image and try again."
            if transient:
                last_error = "eBay image upload was temporarily unavailable."
            if transient and attempt + 1 < retries:
                self.sleeper(0.1 * (2 ** attempt))
                continue
            break
        image.ebay_upload_status = "FAILED"
        image.ebay_upload_error = last_error
        db.session.commit()
        raise MediaServiceError(last_error)

    def upload_listing_images(self, listing: Listing, upload_dir: Path) -> tuple[int, int]:
        if listing.status != ListingStatus.READY:
            raise MediaServiceError("Only an approved READY listing can upload images to eBay.")
        uploaded = skipped = 0
        for image in sorted(listing.images, key=lambda item: item.sort_order):
            if self.upload_image(image, upload_dir / image.filename):
                uploaded += 1
            else:
                skipped += 1
        return uploaded, skipped


def get_media_service(config=None) -> MediaService:
    if config is None:
        from flask import current_app
        config = current_app.config
    return MediaService(config)
