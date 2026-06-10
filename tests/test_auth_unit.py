import pytest
from sqlmodel import SQLModel, Session, create_engine
from sqlmodel.pool import StaticPool
from app import auth


@pytest.fixture
def db():
    engine = create_engine("sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool)
    SQLModel.metadata.create_all(engine)
    with Session(engine) as s:
        yield s


def test_register_authenticate_and_session_lookup(db):
    user = auth.create_user(db, "alice", "pw")
    assert user.id is not None
    assert auth.authenticate(db, "alice", "pw").id == user.id
    assert auth.authenticate(db, "alice", "nope") is None
    token = auth.create_session(db, user)
    assert auth.user_for_token(db, token).id == user.id
    auth.delete_session(db, token)
    assert auth.user_for_token(db, token) is None


def test_duplicate_username_rejected(db):
    auth.create_user(db, "bob", "pw")
    with pytest.raises(auth.UsernameTaken):
        auth.create_user(db, "bob", "other")
