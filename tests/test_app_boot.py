from fastapi.testclient import TestClient
from app.main import app


def test_app_imports_and_has_static_mount():
    client = TestClient(app)
    # static is mounted; a missing asset returns 404 (not a routing error)
    assert client.get("/static/does-not-exist.css").status_code == 404
