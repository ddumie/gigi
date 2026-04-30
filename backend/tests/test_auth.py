from uuid import uuid4


def random_email():
    return f"test+{uuid4().hex[:8]}@example.com"


def auth_headers(token: str) -> dict:
    return {"Authorization": f"Bearer {token}"}


def test_auth_endpoints(client):
    response = client.post("/api/v1/auth/login", json={"email": "test@example.com", "password": "test"})
    assert response.status_code in [200, 400, 401]


def test_register_and_login(client):
    email = random_email()
    password = "testpass"
    register_payload = {
        "email": email,
        "password": password,
        "password_confirm": password,
        "nickname": f"testuser{uuid4().hex[:4]}",
        "name": "Test User"
    }

    register_response = client.post("/api/v1/auth/register", json=register_payload)
    assert register_response.status_code == 201
    data = register_response.json()
    assert "access_token" in data
    assert data["user"]["email"] == email

    login_response = client.post("/api/v1/auth/login", json={"email": email, "password": password})
    assert login_response.status_code == 200
    login_data = login_response.json()
    assert "access_token" in login_data
    assert login_data["user"]["email"] == email

    me_response = client.get("/api/v1/auth/me", headers=auth_headers(login_data["access_token"]))
    assert me_response.status_code == 200
    assert me_response.json()["email"] == email


def test_login_with_invalid_password(client):
    email = random_email()
    password = "correctpass"
    client.post("/api/v1/auth/register", json={
        "email": email,
        "password": password,
        "password_confirm": password,
        "nickname": f"user-{uuid4().hex[:6]}",
        "name": "Test User"
    })

    response = client.post("/api/v1/auth/login", json={"email": email, "password": "wrong"})
    assert response.status_code == 401
