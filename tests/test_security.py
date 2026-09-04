from werkzeug.security import generate_password_hash

from app import create_app


def test_security_defaults_and_upload_limit(app):
    assert app.config["SESSION_COOKIE_HTTPONLY"] is True
    assert app.config["SESSION_COOKIE_SAMESITE"] == "Lax"
    assert app.config["MAX_CONTENT_LENGTH"] == 20 * 1024 * 1024


def test_csrf_blocks_unprotected_post(tmp_path):
    app = create_app({
        "TESTING": True,
        "WTF_CSRF_ENABLED": True,
        "SESSION_COOKIE_SECURE": False,
        "SECRET_KEY": "csrf-test",
        "UPLOAD_DIR": tmp_path / "uploads",
        "SQLALCHEMY_DATABASE_URI": f"sqlite:///{tmp_path / 'csrf.db'}",
        "APP_USERNAME": "admin",
        "APP_PASSWORD_HASH": generate_password_hash("correct horse battery staple"),
    })
    client = app.test_client()
    response = client.post("/login", data={"username": "admin", "password": "correct horse battery staple"})
    assert response.status_code == 400


def test_no_public_registration_route(client):
    assert client.get("/register").status_code == 404
