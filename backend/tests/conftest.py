import os
import pathlib

TEST_DB_PATH = pathlib.Path(__file__).resolve().parent / "test_ci.db"
if TEST_DB_PATH.exists():
    TEST_DB_PATH.unlink()
os.environ.setdefault("DATABASE_URL", f"sqlite:///{TEST_DB_PATH}")
os.environ.setdefault("SECRET_KEY", "test-secret-key")
os.environ.setdefault("ACCESS_TOKEN_EXPIRE_MINUTES", "60")
os.environ.setdefault("GEMINI_API_KEY", "dummy-key")


import pytest
from fastapi.testclient import TestClient


@pytest.fixture(scope="session")
def app():
    import importlib
    import backend.main
    importlib.reload(backend.main)
    return backend.main.app


@pytest.fixture(scope="session")
def client(app):
    with TestClient(app) as client:
        yield client
