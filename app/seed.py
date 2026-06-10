from sqlmodel import Session, select
from .models import Profile, User


def ensure_profile(session: Session, user: User) -> Profile:
    prof = session.exec(select(Profile).where(Profile.user_id == user.id)).first()
    if prof is None:
        prof = Profile(user_id=user.id)
        session.add(prof); session.commit(); session.refresh(prof)
    return prof
