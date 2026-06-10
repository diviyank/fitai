from datetime import date
from typing import Optional
from fastapi import APIRouter, Depends, Request, Form
from fastapi.responses import HTMLResponse, RedirectResponse
from sqlmodel import Session
from ..db import get_session
from ..models import User, PlannedSession, WorkoutLog
from ..auth import current_user
from ..main import templates

router = APIRouter()


def _i(v: str) -> Optional[int]:
    return int(v) if v and v.strip() else None


@router.get("/workouts/session/{session_id}", response_class=HTMLResponse)
def session_page(session_id: int, request: Request, session: Session = Depends(get_session),
                 user: User = Depends(current_user)):
    ps = session.get(PlannedSession, session_id)
    if not ps or ps.user_id != user.id:
        return RedirectResponse("/plan", status_code=303)
    return templates.TemplateResponse("session.html", {
        "request": request, "user": user, "ps": ps})


@router.post("/workouts/log")
def log_workout(session: Session = Depends(get_session), user: User = Depends(current_user),
                planned_session_id: str = Form(""), status: str = Form("done"),
                rpe: str = Form(""), feeling: str = Form(""), notes: str = Form("")):
    session.add(WorkoutLog(
        user_id=user.id, planned_session_id=_i(planned_session_id), date=date.today(),
        status=status, rpe=_i(rpe), feeling=feeling, notes=notes))
    session.commit()
    return RedirectResponse("/plan", status_code=303)
