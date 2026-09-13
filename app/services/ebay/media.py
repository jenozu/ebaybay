"""eBay Media API image upload with local persistence and bounded retries."""
from __future__ import annotations

import hashlib
import time
from pathlib import Path
from urllib.parse import quote, unquote, urlparse

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
        configured = str(self.config.get("EBAY_API_BASE") or "").rstrip("/")
        # The Media API is served from eBay's apim gateway, not the normal
        # REST API host. Preserve custom/mock bases, but translate the two
        # canonical REST hosts so a shared EBAY_API_BASE cannot misroute Media.
        if configured == "https://api.ebay.com":
            return "https://apim.ebay.com"
        if configured == "https://api.sandbox.ebay.com":
            return "https://apim.sandbox.ebay.com"
        if configured:
            return configured
        return (
            "https://apim.sandbox.ebay.com"
            if self.config["EBAY_ENVIRONMENT"].lower() == "sandbox"
            else "https://apim.ebay.com"
        )

    @property
    def endpoint(self) -> str:
        # eBay Media API is a Commerce API and remains on the v1_beta path.
        return f"{self.base_url}/commerce/media/v1_beta/image/create_image_from_file"

    def image_endpoint(self, image_id: str) -> str:
        return f"{self.base_url}/commerce/media/v1_beta/image/{quote(image_id, safe='')}"

    def _headers(self) -> dict[str, str]:
        return {
            "Authorization": f"Bearer {self.token_provider()}",
            "Accept": "application/json",
        }

    @staticmethod
    def _is_transient(response) -> bool:
        status = getattr(response, "status_code", 0)
        return status == 429 or 500 <= status < 600

    @staticmethod
    def _image_id_from_location(response) -> str | None:
        headers = getattr(response, "headers", None)
        location = headers.get("Location") if headers is not None else None
        if not isinstance(location, str) or not location.strip():
            return None
        try:
            path = urlparse(location.strip()).path
        except (TypeError, ValueError):
            return None
        parts = [part for part in path.rstrip("/").split("/") if part]
        if len(parts) < 2 or parts[-2] != "image":
            return None
        image_id = unquote(parts[-1]).strip()
        if not image_id or "/" in image_id or "\\" in image_id:
            return None
        return image_id

    def _get_image_url(self, image_id: str, retries: int) -> str:
        last_error = "eBay image details could not be retrieved."
        for attempt in range(retries):
            try:
                response = self.http.get(
                    self.image_endpoint(image_id),
                    headers=self._headers(),
                    timeout=self.config["EBAY_HTTP_TIMEOUT_SECONDS"],
                )
            except requests.RequestException:
                transient = True
            else:
                transient = self._is_transient(response)
                if getattr(response, "ok", False):
                    try:
                        payload = response.json()
                    except (ValueError, TypeError):
                        raise MediaServiceError("eBay returned an invalid image-details response.")
                    image_url = payload.get("imageUrl") if isinstance(payload, dict) else None
                    if isinstance(image_url, str) and image_url.strip():
                        return image_url.strip()
                    raise MediaServiceError("eBay returned an invalid image-details response.")
                if not transient:
                    raise MediaServiceError("eBay image details could not be retrieved. Check the connection and try again.")
            if transient:
                last_error = "eBay image details were temporarily unavailable."
            if transient and attempt + 1 < retries:
                self.sleeper(0.1 * (2 ** attempt))
                continue
            break
        raise MediaServiceError(last_error)

    @staticmethod
    def _set_uploaded(image: ListingImage, fingerprint: str, image_id: str, image_url: str) -> None:
        image.ebay_image_id = image_id
        image.ebay_image_url = image_url
        image.ebay_upload_fingerprint = fingerprint
        image.ebay_upload_status = "UPLOADED"
        image.ebay_upload_error = None
        image.ebay_uploaded_at = utcnow()
        db.session.commit()

    @staticmethod
    def _set_failed(image: ListingImage, message: str) -> None:
        image.ebay_upload_status = "FAILED"
        image.ebay_upload_error = message
        db.session.commit()

    def upload_image(self, image: ListingImage, path: Path) -> bool:
        if not path.is_file():
            self._set_failed(image, "Local image file is unavailable.")
            raise MediaServiceError("A local listing image is unavailable.")

        content = path.read_bytes()
        fingerprint = hashlib.sha256(content).hexdigest()
        retries = max(1, int(self.config.get("EBAY_MEDIA_MAX_RETRIES", 3)))

        if image.ebay_image_id and image.ebay_upload_fingerprint == fingerprint:
            if image.ebay_image_url:
                image.ebay_upload_status = "UPLOADED"
                image.ebay_upload_error = None
                db.session.commit()
                return False
            # The create call may already have succeeded while getImage failed.
            # Reuse the persisted remote ID rather than creating a duplicate image.
            image.ebay_upload_status = "UPLOADING"
            image.ebay_upload_error = None
            db.session.commit()
            try:
                image_url = self._get_image_url(image.ebay_image_id, retries)
            except MediaServiceError as exc:
                self._set_failed(image, str(exc))
                raise
            self._set_uploaded(image, fingerprint, image.ebay_image_id, image_url)
            return True

        image.ebay_upload_status = "UPLOADING"
        image.ebay_upload_error = None
        db.session.commit()

        last_error = "eBay image upload failed."
        for attempt in range(retries):
            try:
                response = self.http.post(
                    self.endpoint,
                    headers=self._headers(),
                    files={"image": (path.name, content, image.mime_type)},
                    timeout=self.config["EBAY_HTTP_TIMEOUT_SECONDS"],
                )
            except requests.RequestException:
                transient = True
            else:
                transient = self._is_transient(response)
                status = getattr(response, "status_code", 0)
                if getattr(response, "ok", False) and status == 201:
                    image_id = self._image_id_from_location(response)
                    if not image_id:
                        last_error = "eBay returned an invalid image-upload response."
                        transient = False
                    else:
                        # Persist the remote identity before getImage so a transient
                        # detail lookup cannot cause a duplicate create on retry.
                        image.ebay_image_id = image_id
                        image.ebay_upload_fingerprint = fingerprint
                        db.session.commit()
                        try:
                            image_url = self._get_image_url(image_id, retries)
                        except MediaServiceError as exc:
                            self._set_failed(image, str(exc))
                            raise
                        self._set_uploaded(image, fingerprint, image_id, image_url)
                        return True
                elif getattr(response, "ok", False):
                    last_error = "eBay returned an invalid image-upload response."
                    transient = False
                elif not transient:
                    last_error = "eBay rejected the image upload. Check the image and try again."

            if transient:
                last_error = "eBay image upload was temporarily unavailable."
            if transient and attempt + 1 < retries:
                self.sleeper(0.1 * (2 ** attempt))
                continue
            break

        self._set_failed(image, last_error)
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
