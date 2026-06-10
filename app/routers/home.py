from datetime import date
from typing import Optional
from fastapi import APIRouter, Depends, Request
from fastapi.responses import HTMLResponse
from sqlmodel import Session, select
from ..db import get_session
from ..models import User, Profile, Goal, BodyMetric, TrainingPlan, PlannedSession
from ..auth import current_user
from .. import progress
from ..main import templates

router = APIRouter()


def _active_plan(session: Session, user: User) -> Optional[TrainingPlan]:
    return session.exec(
        select(TrainingPlan).where(TrainingPlan.user_id == user.id, TrainingPlan.status == "active")
        .order_by(TrainingPlan.created_at.desc())).first()


@router.get("/", response_class=HTMLResponse)
def dashboard(request: Request, session: Session = Depends(get_session),
              user: User = Depends(current_user)):
    plan = _active_plan(session, user)
    week_sessions, today_session = [], None
    if plan:
        week_sessions = session.exec(
            select(PlannedSession).where(PlannedSession.plan_id == plan.id)
            .order_by(PlannedSession.week_index, PlannedSession.day_index)).all()
        weekday = date.today().isoweekday()
        today_session = next((s for s in week_sessions if s.day_index == weekday), None) \
            or (week_sessions[0] if week_sessions else None)

    metrics = session.exec(
        select(BodyMetric).where(BodyMetric.user_id == user.id).order_by(BodyMetric.date)).all()
    weight_points = [{"x": str(m.date), "y": m.weight_kg} for m in metrics if m.weight_kg is not None]
    trend = progress.weight_trend([{"date": m.date, "weight_kg": m.weight_kg} for m in metrics])

    goal = session.exec(
        select(Goal).where(Goal.user_id == user.id, Goal.status == "active")
        .order_by(Goal.created_at.desc())).first()
    goal_pct = None
    if goal and goal.baseline_value and goal.target_value and trend["current"] is not None:
        goal_pct = round(progress.goal_progress(goal.baseline_value, trend["current"], goal.target_value))

    return templates.TemplateResponse("home.html", {
        "request": request, "user": user, "plan": plan,
        "today_session": today_session, "week_sessions": week_sessions,
        "weight_points": weight_points, "trend": trend, "goal": goal, "goal_pct": goal_pct})
