from datetime import date, datetime
from typing import Optional
from fastapi import APIRouter, Depends, Request, Form
from fastapi.responses import HTMLResponse, RedirectResponse
from sqlmodel import Session, select
from ..db import get_session
from ..models import User, Goal, BodyMetric
from ..auth import current_user
from .. import enums
from ..main import templates

router = APIRouter()


def _f(v: str) -> Optional[float]:
    """Parse a numeric field, tolerating free text (returns None instead of raising)."""
    try:
        return float(v) if v and v.strip() else None
    except ValueError:
        return None


def _date(v: str) -> Optional[date]:
    try:
        return datetime.strptime(v, "%Y-%m-%d").date() if v and v.strip() else None
    except ValueError:
        return None


def _latest_weight(session: Session, user: User) -> Optional[float]:
    row = session.exec(
        select(BodyMetric).where(BodyMetric.user_id == user.id, BodyMetric.weight_kg != None)  # noqa: E711
        .order_by(BodyMetric.date.desc())).first()
    return row.weight_kg if row else None


def active_goal(session: Session, user: User) -> Optional[Goal]:
    return session.exec(
        select(Goal).where(Goal.user_id == user.id, Goal.status == "active")
        .order_by(Goal.created_at.desc())).first()


@router.get("/goals", response_class=HTMLResponse)
def goals_page(request: Request, session: Session = Depends(get_session),
               user: User = Depends(current_user)):
    goals = session.exec(select(Goal).where(Goal.user_id == user.id).order_by(Goal.created_at.desc())).all()
    return templates.TemplateResponse("goals.html", {
        "request": request, "user": user, "goals": goals, "goal_types": enums.GOAL_TYPES})


@router.post("/goals/add")
def add_goal(session: Session = Depends(get_session), user: User = Depends(current_user),
             type: str = Form("general"), target_value: str = Form(""),
             target_date: str = Form(""), baseline_value: str = Form(""), notes: str = Form("")):
    target = _f(target_value)
    notes = notes.strip()
    # A free-text objective (e.g. "perdre du ventre") isn't a number — keep it in notes
    # rather than crashing or silently dropping it.
    if target is None and target_value.strip():
        notes = f"{target_value.strip()}\n{notes}".strip()
    baseline = _f(baseline_value)
    if baseline is None:
        baseline = _latest_weight(session, user)
    goal = Goal(
        user_id=user.id, type=type, target_value=target,
        target_date=_date(target_date), baseline_value=baseline, notes=notes)
    session.add(goal); session.commit()
    return RedirectResponse("/goals", status_code=303)


@router.post("/goals/{goal_id}/retire")
def retire_goal(goal_id: int, session: Session = Depends(get_session),
                user: User = Depends(current_user), status: str = Form("achieved")):
    goal = session.get(Goal, goal_id)
    if goal and goal.user_id == user.id:
        goal.status = status
        session.add(goal); session.commit()
    return RedirectResponse("/goals", status_code=303)
