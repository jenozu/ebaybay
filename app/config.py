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

    EBAY_ENVIRONMENT = os.getenv("EBAY_ENVIRONMENT", "sandbox")
    EBAY_MARKETPLACE_ID = os.getenv("EBAY_MARKETPLACE_ID", "EBAY_CA")
    EBAY_CLIENT_ID = os.getenv("EBAY_CLIENT_ID", "")
    EBAY_CLIENT_SECRET = os.getenv("EBAY_CLIENT_SECRET", "")
    EBAY_RUNAME = os.getenv("EBAY_RUNAME", "")
    EBAY_TOKEN_PATH = Path(os.getenv("EBAY_TOKEN_PATH", "/app/data/token.json"))
