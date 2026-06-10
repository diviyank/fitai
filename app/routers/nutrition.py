from datetime import date
from typing import Optional
from fastapi import APIRouter, Depends, Request, Form, Response
from fastapi.responses import HTMLResponse, RedirectResponse
from sqlmodel import Session, select
from ..db import get_session
from ..models import User, Profile, FoodLog, BodyMetric, Goal
from ..auth import current_user
from .. import enums, nutrition, prompt_builder as pb, response_parser as rp, llm_client
from ..main import templates

router = APIRouter()
FALLBACK_NOTICE = "Estimation directe indisponible — copiez le prompt ci-dessous."


def _i(v: str) -> Optional[int]:
    return int(v) if v and v.strip() else None


def _f(v: str) -> Optional[float]:
    return float(v) if v and v.strip() else None


def _age(birth: Optional[date]) -> Optional[int]:
    if not birth:
        return None
    today = date.today()
    return today.year - birth.year - ((today.month, today.day) < (birth.month, birth.day))


def _today_foods(session: Session, user: User) -> list[FoodLog]:
    return session.exec(
        select(FoodLog).where(FoodLog.user_id == user.id, FoodLog.date == date.today())).all()


def _targets(session: Session, user: User) -> Optional[dict]:
    p = session.exec(select(Profile).where(Profile.user_id == user.id)).first()
    weight_row = session.exec(
        select(BodyMetric).where(BodyMetric.user_id == user.id, BodyMetric.weight_kg != None)  # noqa: E711
        .order_by(BodyMetric.date.desc())).first()
    age = _age(p.birth_date)
    if not (p.height_cm and weight_row and age):
        return None
    goal = session.exec(
        select(Goal).where(Goal.user_id == user.id, Goal.status == "active")
        .order_by(Goal.created_at.desc())).first()
    return nutrition.compute_targets(
        p.sex, age, p.height_cm, weight_row.weight_kg, p.activity_level,
        goal_type=goal.type if goal else None, calorie_override=p.calorie_target_override)


def _totals(foods: list[FoodLog]) -> dict:
    return {
        "calories": sum(f.calories or 0 for f in foods),
        "protein_g": sum(f.protein_g or 0 for f in foods),
        "carbs_g": sum(f.carbs_g or 0 for f in foods),
        "fat_g": sum(f.fat_g or 0 for f in foods),
    }


def _render_page(request, session, user, extra=None):
    foods = _today_foods(session, user)
    ctx = {"request": request, "user": user, "foods": foods, "totals": _totals(foods),
           "targets": _targets(session, user), "meal_slots": enums.MEAL_SLOTS}
    if extra:
        ctx.update(extra)
    return templates.TemplateResponse("nutrition.html", ctx)


@router.get("/nutrition", response_class=HTMLResponse)
def nutrition_page(request: Request, session: Session = Depends(get_session),
                   user: User = Depends(current_user)):
    return _render_page(request, session, user)


@router.post("/nutrition/add")
def add_food(session: Session = Depends(get_session), user: User = Depends(current_user),
             description: str = Form(...), meal_slot: str = Form(None),
             calories: str = Form(""), protein_g: str = Form(""),
             carbs_g: str = Form(""), fat_g: str = Form("")):
    session.add(FoodLog(
        user_id=user.id, date=date.today(), description=description.strip(),
        meal_slot=meal_slot or None, calories=_i(calories), protein_g=_f(protein_g),
        carbs_g=_f(carbs_g), fat_g=_f(fat_g), source="manual"))
    session.commit()
    return RedirectResponse("/nutrition", status_code=303)


@router.post("/nutrition/estimate", response_class=HTMLResponse)
def estimate(request: Request, session: Session = Depends(get_session),
             user: User = Depends(current_user)):
    p = session.exec(select(Profile).where(Profile.user_id == user.id)).first()
    pending = [f for f in _today_foods(session, user) if f.calories is None]
    if not pending:
        return Response(status_code=204, headers={"HX-Redirect": "/nutrition"})
    prompt = pb.build_nutrition_estimate([f.description for f in pending])
    if not (llm_client.is_configured() and p.use_llm_directly):
        return templates.TemplateResponse("partials/_prompt_result.html",
                                          {"request": request, "prompt": prompt, "notice": None})
    try:
        parsed = rp.parse_nutrition_list_response(llm_client.complete(prompt))
    except (llm_client.LLMError, rp.ParseError):
        return templates.TemplateResponse("partials/_prompt_result.html",
                                          {"request": request, "prompt": prompt, "notice": FALLBACK_NOTICE})
    for food, est in zip(pending, parsed.items):
        food.calories = est.calories
        food.protein_g = est.protein_g
        food.carbs_g = est.carbs_g
        food.fat_g = est.fat_g
        food.source = "llm"
        session.add(food)
    session.commit()
    return Response(status_code=204, headers={"HX-Redirect": "/nutrition"})
