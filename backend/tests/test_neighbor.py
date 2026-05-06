def test_neighbor_endpoints(client):
    # Test group search endpoint exists
    response = client.get("/api/v1/neighbor/group-search")
    assert response.status_code in [200, 401]  # Might require auth
