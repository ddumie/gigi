import pytest
from datetime import date, timedelta
from unittest.mock import AsyncMock, MagicMock, patch
from backend.domains.onboarding import crud, service
import pytest


def test_onboarding_preferences_requires_auth(client):
    response = client.get("/api/v1/onboarding/preferences")
    assert response.status_code == 401
    assert isinstance(response.json()["detail"], str)


def test_onboarding_save_preferences_requires_auth(client):
    response = client.post("/api/v1/onboarding/preferences", json={
        "age_group": "20대",
        "health_interests": ["운동"],
        "font_size": 16
    })
    assert response.status_code == 401
    assert isinstance(response.json()["detail"], str)
