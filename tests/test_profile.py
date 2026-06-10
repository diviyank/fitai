import pytest
from sqlmodel import SQLModel, Session, create_engine, select
from sqlmodel.pool import StaticPool
from app import auth
from app.models import Profile


@pytest.fixture
def db():
    engine = create_engine("sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool)
    SQLModel.metadata.create_all(engine)
    with Session(engine) as s:
        yield s


def test_registering_creates_a_profile_with_defaults(db):
    user = auth.create_user(db, "alice", "pw")
    prof = db.exec(select(Profile).where(Profile.user_id == user.id)).first()
    assert prof is not None
    assert prof.language == "fr" and prof.use_llm_directly is True
    assert prof.days_per_week == 3
