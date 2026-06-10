"""Session + identity glue. Pure hashing lives in security.py; this module touches the DB."""
from datetime import datetime, timedelta
from typing import Optional
from fastapi import Depends, Request
from sqlmodel import Session, select
from .db import get_session
from .models import User, UserSession
from .security import hash_password, verify_password, new_token

COOKIE_NAME = "fitai_session"
SESSION_DAYS = 90


class NotAuthenticated(Exception):
    """Raised by current_user when no valid session cookie is present."""


class UsernameTaken(ValueError):
    pass


def create_user(session: Session, username: str, password: str) -> User:
    username = username.strip()
    existing = session.exec(select(User).where(User.username == username)).first()
    if existing is not None:
        raise UsernameTaken(username)
    user = User(username=username, password_hash=hash_password(password))
    session.add(user); session.commit(); session.refresh(user)
    return user


def authenticate(session: Session, username: str, password: str) -> Optional[User]:
    user = session.exec(select(User).where(User.username == username.strip())).first()
    if user and verify_password(password, user.password_hash):
        return user
    return None


def create_session(session: Session, user: User) -> str:
    token = new_token()
    session.add(UserSession(
        user_id=user.id, token=token,
        expires_at=datetime.utcnow() + timedelta(days=SESSION_DAYS)))
    session.commit()
    return token


def user_for_token(session: Session, token: Optional[str]) -> Optional[User]:
    if not token:
        return None
    row = session.exec(select(UserSession).where(UserSession.token == token)).first()
    if row is None or row.expires_at < datetime.utcnow():
        return None
    return session.get(User, row.user_id)


def delete_session(session: Session, token: Optional[str]) -> None:
    if not token:
        return
    row = session.exec(select(UserSession).where(UserSession.token == token)).first()
    if row is not None:
        session.delete(row); session.commit()


def current_user(request: Request, session: Session = Depends(get_session)) -> User:
    token = request.cookies.get(COOKIE_NAME)
    user = user_for_token(session, token)
    if user is None:
        raise NotAuthenticated()
    return user
