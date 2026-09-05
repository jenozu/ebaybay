"""The single seller OAuth/token service used by application eBay clients."""
from __future__ import annotations

import json
from datetime import datetime, timedelta, timezone
from pathlib import Path
from urllib.parse import urlencode

import requests
from cryptography.fernet import Fernet, InvalidToken

from ...extensions import db
from ...models import EbayConnection, utcnow
from .tokens import EbayTokenError


class OAuthError(EbayTokenError):
    """A safe OAuth failure which deliberately contains no token data."""


class OAuthConfigurationError(OAuthError):
    pass


class OAuthRevokedError(OAuthError):
    pass


class OAuthProtocolError(OAuthError):
    pass


# The base API scope supports the currently used Browse/Taxonomy clients, and
# sell.inventory covers the proven seller Inventory API smoke check.
SELLER_SCOPES = (
    "https://api.ebay.com/oauth/api_scope",
    "https://api.ebay.com/oauth/api_scope/sell.inventory",
)


def _utc(value: datetime | None) -> datetime | None:
    if value is None:
        return None
    return value.replace(tzinfo=timezone.utc) if value.tzinfo is None else value.astimezone(timezone.utc)


class OAuthService:
    def __init__(self, config: dict, *, http=None, clock=None):
        self.config = config
        self.http = http or requests
        self.clock = clock or utcnow

    @property
    def environment(self) -> str:
        return self.config["EBAY_ENVIRONMENT"].lower()

    @property
    def authorization_endpoint(self) -> str:
        return "https://auth.sandbox.ebay.com/oauth2/authorize" if self.environment == "sandbox" else "https://auth.ebay.com/oauth2/authorize"

    @property
    def token_endpoint(self) -> str:
        return "https://api.sandbox.ebay.com/identity/v1/oauth2/token" if self.environment == "sandbox" else "https://api.ebay.com/identity/v1/oauth2/token"

    def authorization_url(self, state: str) -> str:
        if not state:
            raise OAuthProtocolError("OAuth state is required.")
        if not self.config.get("EBAY_CLIENT_ID") or not self.config.get("EBAY_RUNAME"):
            raise OAuthConfigurationError("eBay OAuth is not configured. Set the application credentials and RuName.")
        query = urlencode({"client_id": self.config["EBAY_CLIENT_ID"], "redirect_uri": self.config["EBAY_RUNAME"], "response_type": "code", "scope": " ".join(SELLER_SCOPES), "state": state})
        return f"{self.authorization_endpoint}?{query}"

    def _fernet(self) -> Fernet:
        key = self.config.get("EBAY_TOKEN_ENCRYPTION_KEY")
        if not key:
            raise OAuthConfigurationError("eBay token encryption is not configured.")
        try:
            return Fernet(key.encode() if isinstance(key, str) else key)
        except (ValueError, TypeError) as exc:
            raise OAuthConfigurationError("eBay token encryption is configured incorrectly.") from exc

    def _encrypt(self, value: str) -> str:
        return self._fernet().encrypt(value.encode()).decode()

    def _decrypt(self, value: str | None) -> str:
        if not value:
            raise OAuthError("The eBay connection has no usable credential. Reconnect the seller account.")
        try:
            return self._fernet().decrypt(value.encode()).decode()
        except (InvalidToken, UnicodeDecodeError) as exc:
            raise OAuthError("The saved eBay connection cannot be read. Reconnect the seller account.") from exc

    def connection(self, *, create: bool = False) -> EbayConnection | None:
        connection = EbayConnection.query.filter_by(environment=self.environment, marketplace_id=self.config["EBAY_MARKETPLACE_ID"]).one_or_none()
        if connection is None and create:
            connection = EbayConnection(environment=self.environment, marketplace_id=self.config["EBAY_MARKETPLACE_ID"], token_path=str(self.config["EBAY_TOKEN_PATH"]), status="DISCONNECTED")
            db.session.add(connection)
        return connection

    def _expires_at(self, seconds) -> datetime:
        try:
            return self.clock() + timedelta(seconds=max(0, int(seconds)))
        except (TypeError, ValueError) as exc:
            raise OAuthProtocolError("eBay did not return a valid token expiration.") from exc

    def _token_response(self, response) -> dict:
        try:
            data = response.json()
        except (ValueError, TypeError) as exc:
            raise OAuthProtocolError("eBay returned an invalid token response.") from exc
        if not isinstance(data, dict):
            raise OAuthProtocolError("eBay returned an invalid token response.")
        if not getattr(response, "ok", False):
            if str(data.get("error", "")) in {"invalid_grant", "invalid_token", "unauthorized_client"}:
                raise OAuthRevokedError("The eBay authorization is no longer valid. Reconnect the seller account.")
            raise OAuthError("eBay could not refresh the connection. Try again later.")
        return data

    def exchange_code(self, code: str) -> dict:
        if not code:
            raise OAuthProtocolError("No authorization code was provided.")
        try:
            response = self.http.post(self.token_endpoint, auth=(self.config["EBAY_CLIENT_ID"], self.config["EBAY_CLIENT_SECRET"]), headers={"Content-Type": "application/x-www-form-urlencoded"}, data={"grant_type": "authorization_code", "code": code, "redirect_uri": self.config["EBAY_RUNAME"]}, timeout=self.config["EBAY_HTTP_TIMEOUT_SECONDS"])
        except requests.RequestException as exc:
            raise OAuthError("eBay token request failed. Try connecting again.") from exc
        return self._token_response(response)

    def save_token_response(self, payload: dict, *, connection: EbayConnection | None = None, require_refresh: bool = False) -> EbayConnection:
        access_token = payload.get("access_token")
        if not isinstance(access_token, str) or not access_token:
            raise OAuthProtocolError("eBay did not return a usable access token.")
        if require_refresh and not payload.get("refresh_token"):
            raise OAuthProtocolError("eBay did not return a refresh token. Connect again.")
        connection = connection or self.connection(create=True)
        connection.encrypted_access_token = self._encrypt(access_token)
        connection.access_token_expires_at = self._expires_at(payload.get("expires_in"))
        if payload.get("refresh_token"):
            connection.encrypted_refresh_token = self._encrypt(payload["refresh_token"])
            lifetime = payload.get("refresh_token_expires_in")
            connection.refresh_token_expires_at = self._expires_at(lifetime) if lifetime is not None else None
        connection.status = "CONNECTED"
        connection.connected_at = connection.connected_at or self.clock()
        connection.disconnected_at = None
        connection.last_error_code = None
        db.session.commit()
        return connection

    def complete_authorization(self, code: str) -> EbayConnection:
        return self.save_token_response(self.exchange_code(code), require_refresh=True)

    def refresh_access_token(self, connection: EbayConnection) -> str:
        refresh_token = self._decrypt(connection.encrypted_refresh_token)
        try:
            response = self.http.post(self.token_endpoint, auth=(self.config["EBAY_CLIENT_ID"], self.config["EBAY_CLIENT_SECRET"]), headers={"Content-Type": "application/x-www-form-urlencoded"}, data={"grant_type": "refresh_token", "refresh_token": refresh_token, "scope": " ".join(SELLER_SCOPES)}, timeout=self.config["EBAY_HTTP_TIMEOUT_SECONDS"])
            payload = self._token_response(response)
            self.save_token_response(payload, connection=connection)
            return payload["access_token"]
        except OAuthRevokedError:
            self.disconnect(connection, error_code="authorization_revoked")
            raise
        except requests.RequestException as exc:
            raise OAuthError("eBay token refresh failed. Try again later.") from exc

    def get_access_token(self, *, now: datetime | None = None) -> str:
        connection = self.connection()
        if connection is None or connection.status != "CONNECTED":
            raise OAuthError("eBay is disconnected. Connect the seller account in Settings.")
        now = _utc(now or self.clock())
        expiry = _utc(connection.access_token_expires_at)
        margin = timedelta(seconds=int(self.config.get("EBAY_OAUTH_REFRESH_MARGIN_SECONDS", 300)))
        if expiry and expiry > now + margin:
            return self._decrypt(connection.encrypted_access_token)
        return self.refresh_access_token(connection)

    def has_usable_connection(self) -> bool:
        connection = self.connection()
        if connection is None or connection.status != "CONNECTED":
            return False
        try:
            self._decrypt(connection.encrypted_access_token)
            return bool(connection.encrypted_refresh_token)
        except OAuthError:
            return False

    def import_legacy_token(self) -> EbayConnection | None:
        """One-time compatibility import; old file remains until explicit disconnect."""
        if self.connection() is not None:
            return self.connection()
        try:
            payload = json.loads(Path(self.config["EBAY_TOKEN_PATH"]).read_text(encoding="utf-8"))
        except (OSError, ValueError, json.JSONDecodeError):
            return None
        connection = self.save_token_response(payload, require_refresh=bool(payload.get("refresh_token")))
        connection.legacy_imported_at = self.clock()
        db.session.commit()
        return connection

    def disconnect(self, connection: EbayConnection | None = None, *, error_code: str | None = None) -> None:
        connection = connection or self.connection(create=True)
        connection.status = "DISCONNECTED"
        connection.encrypted_access_token = connection.encrypted_refresh_token = None
        connection.access_token_expires_at = connection.refresh_token_expires_at = None
        connection.disconnected_at = self.clock()
        connection.last_error_code = error_code
        db.session.commit()
        Path(connection.token_path or self.config["EBAY_TOKEN_PATH"]).unlink(missing_ok=True)


def get_oauth_service(config=None) -> OAuthService:
    if config is None:
        from flask import current_app
        config = current_app.config
    return OAuthService(config)
