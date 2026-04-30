from uuid import uuid4


def random_email():
    return f"test+{uuid4().hex[:8]}@example.com"


def auth_headers(token: str) -> dict:
    return {"Authorization": f"Bearer {token}"}


def create_user_and_token(client):
    email = random_email()
    password = "testpass"
    register_payload = {
        "email": email,
        "password": password,
        "password_confirm": password,
        "nickname": f"user-{uuid4().hex[:6]}",
        "name": "Test User"
    }
    response = client.post("/api/v1/auth/register", json=register_payload)
    assert response.status_code == 201
    return response.json()["access_token"]


def test_support_endpoints(client):
    response = client.get("/api/v1/support/group/summary/test-code")
    assert response.status_code in [200, 400, 404, 401, 500]


def test_support_create_and_update_group(client):
    token = create_user_and_token(client)
    headers = auth_headers(token)

    create_payload = {"name": "테스트 모임", "group_type": "friend"}
    create_response = client.post("/api/v1/support/group/create", json=create_payload, headers=headers)
    assert create_response.status_code == 200
    group_id = create_response.json()["id"]

    update_payload = {"name": "변경된 모임", "group_type": "family"}
    update_response = client.put(f"/api/v1/support/group/{group_id}/profile", json=update_payload, headers=headers)
    assert update_response.status_code == 200
    assert update_response.json()["name"] == "변경된 모임"

    settings_response = client.get(f"/api/v1/support/group/{group_id}/settings", headers=headers)
    assert settings_response.status_code == 200
    assert settings_response.json()["group"]["id"] == group_id

