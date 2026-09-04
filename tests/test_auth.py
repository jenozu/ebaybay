def test_dashboard_requires_login(client):
    response = client.get("/dashboard")
    assert response.status_code == 302
    assert "/login" in response.headers["Location"]


def test_login_success(client):
    response = client.post("/login", data={"username": "admin", "password": "correct horse battery staple"}, follow_redirects=True)
    assert response.status_code == 200
    assert b"Listings" in response.data


def test_login_rejects_wrong_password(client):
    response = client.post("/login", data={"username": "admin", "password": "wrong"}, follow_redirects=True)
    assert b"Invalid username or password" in response.data
