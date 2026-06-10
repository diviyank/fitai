from datetime import date, datetime
from typing import Optional
from fastapi import APIRouter, Depends, Request, Form
from fastapi.responses import RedirectResponse, HTMLResponse
from sqlmodel import Session, select
from ..db import get_session
from ..models import User, Profile
from ..auth import current_user
from .. import enums, llm_client
from ..main import templates

router = APIRouter()


def _profile(session: Session, user: User) -> Profile:
    return session.exec(select(Profile).where(Profile.user_id == user.id)).first()


def _parse_date(value: str) -> Optional[date]:
    return datetime.strptime(value, "%Y-%m-%d").date() if value else None


def _parse_float(value: str) -> Optional[float]:
    return float(value) if value.strip() else None


def _parse_int(value: str) -> Optional[int]:
    return int(value) if value.strip() else None


@router.get("/settings", response_class=HTMLResponse)
def settings_page(request: Request, session: Session = Depends(get_session),
                  user: User = Depends(current_user)):
    return templates.TemplateResponse("settings.html", {
        "request": request, "user": user, "profile": _profile(session, user),
        "sexes": enums.SEXES, "activity_levels": enums.ACTIVITY_LEVELS,
        "api_configured": llm_client.is_configured(),
    })


@router.post("/settings")
def update_settings(
    session: Session = Depends(get_session), user: User = Depends(current_user),
    sex: str = Form("homme"), birth_date: str = Form(""), height_cm: str = Form(""),
    activity_level: str = Form("modere"), language: str = Form("fr"),
    medical_conditions: str = Form(""), preferences: str = Form(""), equipment: str = Form(""),
    days_per_week: int = Form(3), session_length_min: int = Form(45),
    calorie_target_override: str = Form(""), use_llm_directly: str = Form(None),
):
    p = _profile(session, user)
    p.sex = sex
    p.birth_date = _parse_date(birth_date)
    p.height_cm = _parse_float(height_cm)
    p.activity_level = activity_level
    p.language = language
    p.medical_conditions = medical_conditions
    p.preferences = preferences
    p.equipment = equipment
    p.days_per_week = days_per_week
    p.session_length_min = session_length_min
    p.calorie_target_override = _parse_int(calorie_target_override)
    p.use_llm_directly = use_llm_directly is not None
    session.add(p); session.commit()
    return RedirectResponse("/settings", status_code=303)
