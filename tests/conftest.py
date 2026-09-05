import pytest
from werkzeug.security import generate_password_hash

from app import create_app
from app.extensions import db


@pytest.fixture()
def app(tmp_path):
    database = tmp_path / "test.db"
    uploads = tmp_path / "uploads"
    token = tmp_path / "token.json"
    app = create_app({"TESTING": True, "WTF_CSRF_ENABLED": False, "SESSION_COOKIE_SECURE": False, "SECRET_KEY": "test-secret", "SQLALCHEMY_DATABASE_URI": f"sqlite:///{database}", "UPLOAD_DIR": uploads, "APP_USERNAME": "admin", "APP_PASSWORD_HASH": generate_password_hash("correct horse battery staple"), "EBAY_CLIENT_ID": "client-id", "EBAY_CLIENT_SECRET": "client-secret", "EBAY_RUNAME": "runame", "EBAY_TOKEN_PATH": token, "EBAY_TOKEN_ENCRYPTION_KEY": "OUQxY9tKooYQgtzMO1FCPaOeT8VGdrz7BpwVeODDcQY="})
    with app.app_context():
        db.create_all()
    yield app
    with app.app_context():
        db.session.remove()
        db.drop_all()


@pytest.fixture()
def client(app):
    return app.test_client()


@pytest.fixture()
def login(client):
    def _login():
        return client.post("/login", data={"username": "admin", "password": "correct horse battery staple"}, follow_redirects=True)
    return _login
