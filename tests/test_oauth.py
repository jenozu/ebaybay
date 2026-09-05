from datetime import timedelta
from urllib.parse import parse_qs, urlparse

import pytest

from app.extensions import db
from app.models import EbayConnection, utcnow
from app.services.ebay.oauth import OAuthConfigurationError, OAuthProtocolError, OAuthRevokedError, OAuthService


class FakeResponse:
    def __init__(self, payload, ok=True): self.payload, self.ok = payload, ok
    def json(self): return self.payload


class FakeHttp:
    def __init__(self, responses): self.responses, self.calls = list(responses), []
    def post(self, *args, **kwargs):
        self.calls.append((args, kwargs))
        return self.responses.pop(0)


def token_payload(access="access-token", refresh="refresh-token", expires=7200):
    return {"access_token": access, "refresh_token": refresh, "expires_in": expires, "refresh_token_expires_in": 47304000}


def test_authorization_url_uses_sandbox_and_required_state(app):
    with app.app_context(): url = OAuthService(app.config).authorization_url("csrf-state")
    parsed, query = urlparse(url), parse_qs(urlparse(url).query)
    assert parsed.netloc == "auth.sandbox.ebay.com"
    assert query["state"] == ["csrf-state"] and query["response_type"] == ["code"]
    assert "sell.inventory" in query["scope"][0]


def test_missing_encryption_key_fails_safely(app):
    app.config["EBAY_TOKEN_ENCRYPTION_KEY"] = ""
    with app.app_context(), pytest.raises(OAuthConfigurationError):
        OAuthService(app.config).save_token_response(token_payload(), require_refresh=True)


def test_tokens_are_encrypted_and_legacy_import_is_one_time(app):
    app.config["EBAY_TOKEN_PATH"].write_text('{"access_token":"legacy-access","refresh_token":"legacy-refresh","expires_in":7200}')
    with app.app_context():
        service = OAuthService(app.config)
        connection = service.import_legacy_token()
        assert connection.status == "CONNECTED"
        assert "legacy-refresh" not in connection.encrypted_refresh_token
        assert service.get_access_token() == "legacy-access"
        assert app.config["EBAY_TOKEN_PATH"].exists()


def test_unexpired_token_reused_near_expiry_refreshed_and_metadata_saved(app):
    with app.app_context():
        service = OAuthService(app.config)
        connection = service.save_token_response(token_payload("old", "refresh", 7200), require_refresh=True)
        assert service.get_access_token() == "old"
        connection.access_token_expires_at = utcnow() + timedelta(seconds=20)
        db.session.commit()
        refreshed = OAuthService(app.config, http=FakeHttp([FakeResponse(token_payload("new", "rotated", 7200))]))
        assert refreshed.get_access_token() == "new"
        assert refreshed._decrypt(connection.encrypted_refresh_token) == "rotated"


def test_revoked_refresh_disconnects_and_clears_credentials(app):
    with app.app_context():
        service = OAuthService(app.config)
        connection = service.save_token_response(token_payload(expires=0), require_refresh=True)
        revoked = OAuthService(app.config, http=FakeHttp([FakeResponse({"error": "invalid_grant"}, ok=False)]))
        with pytest.raises(OAuthRevokedError): revoked.get_access_token()
        assert connection.status == "DISCONNECTED" and connection.encrypted_refresh_token is None
        assert connection.last_error_code == "authorization_revoked"


def test_code_exchange_uses_documented_endpoint_and_rejects_malformed_response(app):
    with app.app_context():
        http = FakeHttp([FakeResponse(token_payload())])
        assert OAuthService(app.config, http=http).exchange_code("one-time-code")["access_token"] == "access-token"
        args, kwargs = http.calls[0]
        assert args[0] == "https://api.sandbox.ebay.com/identity/v1/oauth2/token"
        assert kwargs["data"] == {"grant_type": "authorization_code", "code": "one-time-code", "redirect_uri": "runame"}
        with pytest.raises(OAuthProtocolError):
            OAuthService(app.config, http=FakeHttp([FakeResponse({})])).save_token_response({}, require_refresh=True)


def test_connect_callback_state_is_required_one_time_and_never_leaks_tokens(client, login, monkeypatch):
    login()
    connect = client.post("/settings/ebay/connect")
    state = parse_qs(urlparse(connect.location).query)["state"][0]
    calls = []
    class Service:
        def authorization_url(self, state): return f"https://example.test/?state={state}"
        def complete_authorization(self, code): calls.append(code)
    monkeypatch.setattr("app.oauth.get_oauth_service", lambda: Service())
    assert client.get("/oauth/callback?code=secret-code&state=wrong").status_code == 400
    assert client.get(f"/oauth/callback?code=secret-code&state={state}").status_code == 400
    client.post("/settings/ebay/connect")
    with client.session_transaction() as session: valid_state = session["ebay_oauth_state"]
    good = client.get(f"/oauth/callback?code=secret-code&state={valid_state}")
    assert good.status_code == 302 and calls == ["secret-code"] and b"secret-code" not in good.data


def test_callback_denial_missing_state_and_settings_auth_disconnect(client, login, app, monkeypatch):
    assert client.get("/settings/ebay").status_code == 302
    login()
    monkeypatch.setattr("app.oauth.get_oauth_service", lambda: pytest.fail("should not exchange"))
    assert client.get("/oauth/callback?error=access_denied").status_code == 400
    monkeypatch.undo()
    assert b"Disconnected" in client.get("/settings/ebay").data
    with app.app_context(): OAuthService(app.config).save_token_response(token_payload(), require_refresh=True)
    assert b"Connected" in client.get("/settings/ebay").data
    assert client.post("/settings/ebay/disconnect").status_code == 302
    with app.app_context(): assert EbayConnection.query.one().status == "DISCONNECTED"


def test_client_provider_uses_shared_service(app):
    with app.app_context():
        OAuthService(app.config).save_token_response(token_payload(), require_refresh=True)
        from app.listings import _browse_client, _taxonomy_client
        assert _browse_client().access_token_provider() == "access-token"
        assert _taxonomy_client().access_token_provider() == "access-token"
