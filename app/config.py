import os
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
    EBAY_TITLE_MAX_LENGTH = int(os.getenv("EBAY_TITLE_MAX_LENGTH", "80"))
    EBAY_LISTING_FORMAT = os.getenv("EBAY_LISTING_FORMAT", "FIXED_PRICE")
    EBAY_PAYMENT_POLICY_ID = os.getenv("EBAY_PAYMENT_POLICY_ID", "")
    EBAY_FULFILLMENT_POLICY_ID = os.getenv("EBAY_FULFILLMENT_POLICY_ID", "")
    EBAY_RETURN_POLICY_ID = os.getenv("EBAY_RETURN_POLICY_ID", "")
    EBAY_MERCHANT_LOCATION_KEY = os.getenv("EBAY_MERCHANT_LOCATION_KEY", "")
