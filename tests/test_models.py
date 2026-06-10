from datetime import datetime
from app.models import User, UserSession


def test_user_and_session_fields():
    u = User(username="alice", password_hash="x")
    assert u.username == "alice"
    s = UserSession(user_id=1, token="tok", expires_at=datetime(2030, 1, 1))
    assert s.user_id == 1 and s.token == "tok"
