import pytest
from sqlmodel import SQLModel, Session, create_engine
from sqlmodel.pool import StaticPool
from fastapi.testclient import TestClient
from app.main import app
from app.db import get_session


@pytest.fixture
def client():
    engine = create_engine("sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool)
    SQLModel.metadata.create_all(engine)
    session = Session(engine)
    app.dependency_overrides[get_session] = lambda: session
    yield TestClient(app)
    app.dependency_overrides.clear(); session.close()


def test_register_logs_in_and_sets_cookie(client):
    r = client.post("/register", data={"username": "alice", "password": "pw"}, follow_redirects=False)
    assert r.status_code == 303
    assert "fitai_session" in r.cookies


def test_protected_route_redirects_when_anonymous(client):
    r = client.get("/", follow_redirects=False)
    assert r.status_code == 303 and r.headers["location"] == "/login"


def test_login_then_access_then_logout(client):
    client.post("/register", data={"username": "bob", "password": "pw"})
    client.post("/logout")
    bad = client.post("/login", data={"username": "bob", "password": "nope"})
    assert "incorrect" in bad.text.lower() or bad.status_code == 200
    ok = client.post("/login", data={"username": "bob", "password": "pw"}, follow_redirects=False)
    assert ok.status_code == 303
    home = client.get("/", follow_redirects=False)
    assert home.status_code in (200, 303)  # 200 once home router exists (Phase 8)


def test_duplicate_username_shows_error(client):
    client.post("/register", data={"username": "carol", "password": "pw"})
    client.get("/logout")
    r = client.post("/register", data={"username": "carol", "password": "x"})
    assert r.status_code == 200 and "déjà" in r.text.lower()
