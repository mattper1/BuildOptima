def test_register_returns_201_with_tokens(client):
    res = client.post(
        "/auth/register",
        json={"email": "user@example.com", "password": "password123"},
    )
    assert res.status_code == 201
    body = res.json()
    assert "access_token" in body
    assert "refresh_token" in body
    assert body["token_type"] == "bearer"


def test_register_duplicate_email_returns_400(client):
    payload = {"email": "dup@example.com", "password": "password123"}
    client.post("/auth/register", json=payload)
    res = client.post("/auth/register", json=payload)
    assert res.status_code == 400


def test_register_short_password_returns_422(client):
    res = client.post(
        "/auth/register", json={"email": "user@example.com", "password": "short"}
    )
    assert res.status_code == 422


def test_login_valid_credentials_returns_tokens(client):
    client.post(
        "/auth/register",
        json={"email": "user@example.com", "password": "password123"},
    )
    res = client.post(
        "/auth/login",
        json={"email": "user@example.com", "password": "password123"},
    )
    assert res.status_code == 200
    assert "access_token" in res.json()
    assert "refresh_token" in res.json()


def test_login_wrong_password_returns_401(client):
    client.post(
        "/auth/register",
        json={"email": "user@example.com", "password": "password123"},
    )
    res = client.post(
        "/auth/login",
        json={"email": "user@example.com", "password": "wrongpass"},
    )
    assert res.status_code == 401


def test_login_unknown_email_returns_401(client):
    res = client.post(
        "/auth/login",
        json={"email": "ghost@example.com", "password": "password123"},
    )
    assert res.status_code == 401


def test_refresh_returns_new_access_token_only(client):
    reg = client.post(
        "/auth/register",
        json={"email": "user@example.com", "password": "password123"},
    )
    refresh_token = reg.json()["refresh_token"]
    res = client.post("/auth/refresh", json={"refresh_token": refresh_token})
    assert res.status_code == 200
    body = res.json()
    assert "access_token" in body
    assert "refresh_token" not in body


def test_refresh_with_access_token_returns_401(client):
    reg = client.post(
        "/auth/register",
        json={"email": "user@example.com", "password": "password123"},
    )
    access_token = reg.json()["access_token"]
    res = client.post("/auth/refresh", json={"refresh_token": access_token})
    assert res.status_code == 401
