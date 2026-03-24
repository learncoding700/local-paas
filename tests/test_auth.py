def test_register_new_user_success(client):
    r = client.post("/auth/register", json={"username": "newuser", "password": "pass123"})
    assert r.status_code == 200
    assert "message" in r.json()


def test_register_duplicate_username_fails(client):
    body = {"username": "dupuser", "password": "pass123"}
    assert client.post("/auth/register", json=body).status_code == 200
    assert client.post("/auth/register", json=body).status_code == 400


def test_register_missing_fields_returns_422(client):
    r = client.post("/auth/register", json={})
    assert r.status_code == 422


def test_login_with_correct_credentials(client):
    client.post("/auth/register", json={"username": "loguser", "password": "secret123"})
    r = client.post("/auth/login", json={"username": "loguser", "password": "secret123"})
    assert r.status_code == 200
    body = r.json()
    assert "access_token" in body
    assert body["token_type"] == "bearer"


def test_login_with_wrong_password_fails(client):
    client.post("/auth/register", json={"username": "wpuser", "password": "rightpass"})
    r = client.post("/auth/login", json={"username": "wpuser", "password": "wrongpass"})
    assert r.status_code == 401


def test_login_with_nonexistent_user_fails(client):
    r = client.post("/auth/login", json={"username": "nobody_xyz", "password": "any"})
    assert r.status_code == 401


def test_protected_route_without_token_returns_401(client):
    r = client.get("/containers")
    assert r.status_code == 401


def test_protected_route_with_valid_token_returns_200(client, auth_headers):
    r = client.get("/containers", headers=auth_headers)
    assert r.status_code == 200
