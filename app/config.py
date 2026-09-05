import os
import logging
from pathlib import Path


class Config:
    SECRET_KEY = os.getenv("SECRET_KEY", "change-me-before-production")
    SQLALCHEMY_DATABASE_URI = os.getenv("DATABASE_URL", "sqlite:////app/data/app.db")
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    UPLOAD_DIR = Path(os.getenv("UPLOAD_DIR", "/app/uploads"))
    MAX_CONTENT_LENGTH = int(os.getenv("MAX_UPLOAD_BYTES", str(20 * 1024 * 1024)))
    ALLOWED_IMAGE_EXTENSIONS = {"jpg", "jpeg", "png", "webp"}
    ALLOWED_IMAGE_MIME_TYPES = {"image/jpeg", "image/png", "image/webp"}

    APP_USERNAME = os.getenv("APP_USERNAME", "admin")
    APP_PASSWORD_HASH = os.getenv("APP_PASSWORD_HASH", "")

    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = "Lax"
    SESSION_COOKIE_SECURE = os.getenv("SESSION_COOKIE_SECURE", "true").lower() == "true"
    WTF_CSRF_TIME_LIMIT = None

    AI_PROVIDER = os.getenv("AI_PROVIDER", "openai")
    AI_API_KEY = os.getenv("AI_API_KEY", "")
    AI_MODEL = os.getenv("AI_MODEL", "")
    AI_API_BASE = os.getenv("AI_API_BASE", "https://api.openai.com/v1")
    AI_TIMEOUT_SECONDS = int(os.getenv("AI_TIMEOUT_SECONDS", "90"))

    EBAY_ENVIRONMENT = os.getenv("EBAY_ENVIRONMENT", "sandbox")
    EBAY_MARKETPLACE_ID = os.getenv("EBAY_MARKETPLACE_ID", "EBAY_CA")
    EBAY_CURRENCY = os.getenv("EBAY_CURRENCY", "CAD").upper()
    EBAY_CLIENT_ID = os.getenv("EBAY_CLIENT_ID", "")
    EBAY_CLIENT_SECRET = os.getenv("EBAY_CLIENT_SECRET", "")
    EBAY_RUNAME = os.getenv("EBAY_RUNAME", "")
    EBAY_TOKEN_PATH = Path(os.getenv("EBAY_TOKEN_PATH", "/app/data/token.json"))
    EBAY_TOKEN_ENCRYPTION_KEY = os.getenv("EBAY_TOKEN_ENCRYPTION_KEY", "")
    EBAY_OAUTH_REFRESH_MARGIN_SECONDS = int(os.getenv("EBAY_OAUTH_REFRESH_MARGIN_SECONDS", "300"))
    EBAY_API_BASE = os.getenv("EBAY_API_BASE", "")
    EBAY_HTTP_TIMEOUT_SECONDS = int(os.getenv("EBAY_HTTP_TIMEOUT_SECONDS", "30"))
    EBAY_MEDIA_MAX_RETRIES = int(os.getenv("EBAY_MEDIA_MAX_RETRIES", "3"))
    EBAY_LISTING_DURATION = os.getenv("EBAY_LISTING_DURATION", "GTC")
    EBAY_TITLE_MAX_LENGTH = int(os.getenv("EBAY_TITLE_MAX_LENGTH", "80"))
    EBAY_LISTING_FORMAT = os.getenv("EBAY_LISTING_FORMAT", "FIXED_PRICE")
    EBAY_PAYMENT_POLICY_ID = os.getenv("EBAY_PAYMENT_POLICY_ID", "")
    EBAY_FULFILLMENT_POLICY_ID = os.getenv("EBAY_FULFILLMENT_POLICY_ID", "")
    EBAY_RETURN_POLICY_ID = os.getenv("EBAY_RETURN_POLICY_ID", "")
    EBAY_MERCHANT_LOCATION_KEY = os.getenv("EBAY_MERCHANT_LOCATION_KEY", "")
    APP_LOG_LEVEL = os.getenv("APP_LOG_LEVEL", "INFO").upper()
    BACKUP_DIR = Path(os.getenv("BACKUP_DIR", "/app/data/backups"))
    BACKUP_RETENTION_DAYS = int(os.getenv("BACKUP_RETENTION_DAYS", "14"))
    UPLOAD_RETENTION_DAYS = int(os.getenv("UPLOAD_RETENTION_DAYS", "30"))


def validate_production_config(config: dict) -> None:
    """Fail closed on unsafe Production startup; Sandbox remains convenient locally."""
    environment = str(config.get("EBAY_ENVIRONMENT", "")).lower()
    if environment not in {"sandbox", "production"}:
        raise RuntimeError("EBAY_ENVIRONMENT must be sandbox or production.")
    if environment != "production":
        return
    missing = []
    if not config.get("SECRET_KEY") or config.get("SECRET_KEY") == "change-me-before-production": missing.append("SECRET_KEY")
    if not config.get("APP_PASSWORD_HASH"): missing.append("APP_PASSWORD_HASH")
    if not config.get("SESSION_COOKIE_SECURE"): missing.append("SESSION_COOKIE_SECURE=true")
    if config.get("DEBUG"): missing.append("DEBUG=false")
    for name in ("EBAY_CLIENT_ID", "EBAY_CLIENT_SECRET", "EBAY_RUNAME", "EBAY_TOKEN_ENCRYPTION_KEY"):
        if not config.get(name): missing.append(name)
    if config.get("EBAY_MARKETPLACE_ID") != "EBAY_CA": missing.append("EBAY_MARKETPLACE_ID=EBAY_CA")
    if missing:
        raise RuntimeError("Unsafe Production configuration: " + ", ".join(missing))


class SecretRedactingFilter(logging.Filter):
    _markers = ("access_token", "refresh_token", "client_secret", "authorization", "bearer ")

    def filter(self, record) -> bool:
        message = record.getMessage()
        if any(marker in message.lower() for marker in self._markers):
            record.msg, record.args = "Sensitive eBay credential data redacted.", ()
        return True


def configure_logging(config: dict) -> None:
    handler = logging.StreamHandler()
    handler.addFilter(SecretRedactingFilter())
    handler.setFormatter(logging.Formatter('{"time":"%(asctime)s","level":"%(levelname)s","logger":"%(name)s","message":"%(message)s"}'))
    root = logging.getLogger()
    if not any(getattr(existing, "_ebaybay", False) for existing in root.handlers):
        handler._ebaybay = True
        root.addHandler(handler)
    root.setLevel(getattr(logging, config.get("APP_LOG_LEVEL", "INFO"), logging.INFO))
