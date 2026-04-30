def test_today_endpoints(client):
    # Test today endpoint exists
    response = client.get("/api/v1/today/")
    assert response.status_code in [200, 401]  # Might require auth
