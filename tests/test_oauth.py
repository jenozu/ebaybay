import json


class FakeResponse:
    ok = True
    def json(self):
        return {"access_token": "access", "refresh_token": "refresh", "expires_in": 7200}


def test_oauth_callback_regression(client, app, monkeypatch):
    calls = {}
    def fake_post(url, auth, headers, data, timeout):
        calls.update(url=url, auth=auth, data=data)
        return FakeResponse()
    monkeypatch.setattr("app.oauth.requests.post", fake_post)
    response = client.get("/oauth/callback?code=fresh-code")
    assert response.status_code == 200
    assert b"eBay OAuth Success" in response.data
    token_path = app.config["EBAY_TOKEN_PATH"]
    assert token_path.exists()
    saved = json.loads(token_path.read_text())
    assert saved["refresh_token"] == "refresh"
    assert calls["auth"] == ("client-id", "client-secret")
    assert calls["data"]["redirect_uri"] == "runame"


def test_oauth_callback_requires_code(client):
    response = client.get("/oauth/callback")
    assert response.status_code == 400
