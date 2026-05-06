def test_habits_endpoints(client):
    # Test habits endpoint exists
    response = client.get("/api/v1/habits/")
    assert response.status_code in [200, 401]  # Might require auth
