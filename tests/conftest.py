import pytest
from sqlmodel import SQLModel, Session, create_engine
from sqlmodel.pool import StaticPool
from fastapi.testclient import TestClient
from app.main import app
from app.db import get_session
from app import auth


@pytest.fixture
def session():
    engine = create_engine("sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool)
    SQLModel.metadata.create_all(engine)
    with Session(engine) as s:
        yield s


@pytest.fixture
def client(session):
    app.dependency_overrides[get_session] = lambda: session
    yield TestClient(app)
    app.dependency_overrides.clear()


@pytest.fixture
def user(session):
    return auth.create_user(session, "tester", "pw")


@pytest.fixture
def authed(client, user, session):
    """A TestClient carrying a valid session cookie for `user`."""
    token = auth.create_session(session, user)
    client.cookies.set(auth.COOKIE_NAME, token)
    return client


@pytest.fixture
def fake_llm(monkeypatch):
    """Force the direct-LLM path on and stub the Anthropic call.

    Set state['reply'] to a JSON string for success, or to an LLMError instance for failure.
    state['calls'] counts invocations; state['prompts'] records each prompt sent."""
    from app import llm_client
    state = {"reply": "", "prompts": [], "calls": 0}

    def _complete(prompt):
        state["calls"] += 1
        state["prompts"].append(prompt)
        if isinstance(state["reply"], Exception):
            raise state["reply"]
        return state["reply"]

    monkeypatch.setattr(llm_client, "is_configured", lambda: True)
    monkeypatch.setattr(llm_client, "complete", _complete)
    return state
