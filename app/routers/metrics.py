from datetime import date, datetime
from typing import Optional
from fastapi import APIRouter, Depends, Request, Form
from fastapi.responses import HTMLResponse, RedirectResponse
from sqlmodel import Session, select
from ..db import get_session
from ..models import User, BodyMetric
from ..auth import current_user
from ..main import templates

router = APIRouter()


def _f(value: str) -> Optional[float]:
    return float(value) if value and value.strip() else None


def _i(value: str) -> Optional[int]:
    return int(value) if value and value.strip() else None


def _today_row(session: Session, user: User) -> Optional[BodyMetric]:
    return session.exec(
        select(BodyMetric).where(BodyMetric.user_id == user.id, BodyMetric.date == date.today())
    ).first()


def _history(session: Session, user: User) -> list[BodyMetric]:
    return session.exec(
        select(BodyMetric).where(BodyMetric.user_id == user.id).order_by(BodyMetric.date.desc())
    ).all()


@router.get("/metrics", response_class=HTMLResponse)
def metrics_page(request: Request, session: Session = Depends(get_session),
                 user: User = Depends(current_user)):
    return templates.TemplateResponse("metrics.html", {
        "request": request, "user": user, "history": _history(session, user)})


@router.get("/metrics/quick", response_class=HTMLResponse)
def quick_form(request: Request, session: Session = Depends(get_session),
               user: User = Depends(current_user)):
    """Prefilled quick-add form for the FAB, lazy-loaded via htmx so today's row shows."""
    return templates.TemplateResponse("partials/_quick_form.html", {
        "request": request, "user": user, "today": _today_row(session, user)})


@router.post("/metrics/quick")
def quick_add(request: Request, session: Session = Depends(get_session),
              user: User = Depends(current_user),
              weight_kg: str = Form(""), steps: str = Form(""), energy: str = Form(""),
              sleep_hours: str = Form("")):
    row = _today_row(session, user) or BodyMetric(user_id=user.id, date=date.today())
    if _f(weight_kg) is not None: row.weight_kg = _f(weight_kg)
    if _i(steps) is not None: row.steps = _i(steps)
    if _i(energy) is not None: row.energy = _i(energy)
    if _f(sleep_hours) is not None: row.sleep_hours = _f(sleep_hours)
    session.add(row); session.commit()
    return RedirectResponse("/metrics", status_code=303)


@router.post("/metrics/add")
def add_metric(request: Request, session: Session = Depends(get_session),
               user: User = Depends(current_user),
               entry_date: str = Form(""), weight_kg: str = Form(""), steps: str = Form(""),
               body_fat_pct: str = Form(""), energy: str = Form(""),
               sleep_hours: str = Form(""), soreness: str = Form(""), notes: str = Form("")):
    day = datetime.strptime(entry_date, "%Y-%m-%d").date() if entry_date else date.today()
    row = session.exec(
        select(BodyMetric).where(BodyMetric.user_id == user.id, BodyMetric.date == day)).first()
    row = row or BodyMetric(user_id=user.id, date=day)
    for field, raw, conv in [
        ("weight_kg", weight_kg, _f), ("steps", steps, _i), ("body_fat_pct", body_fat_pct, _f),
        ("energy", energy, _i), ("sleep_hours", sleep_hours, _f), ("soreness", soreness, _i)]:
        val = conv(raw)
        if val is not None: setattr(row, field, val)
    row.notes = notes or row.notes
    session.add(row); session.commit()
    return RedirectResponse("/metrics", status_code=303)
