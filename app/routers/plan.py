from datetime import date
from typing import Optional
from fastapi import APIRouter, Depends, Request, Form, Response
from fastapi.responses import HTMLResponse, RedirectResponse
from sqlmodel import Session, select
from ..db import get_session
from ..models import User, Profile, Goal, BodyMetric, WorkoutLog, TrainingPlan, PlannedSession
from ..auth import current_user
from .. import prompt_builder as pb, response_parser as rp, llm_client
from ..progress import build_context_summary
from ..main import templates

router = APIRouter()
FALLBACK_NOTICE = "Génération directe indisponible — copiez le prompt ci-dessous."
CONTEXT_WINDOW_DAYS = 14


def _age(birth: Optional[date]) -> Optional[int]:
    if not birth:
        return None
    today = date.today()
    return today.year - birth.year - ((today.month, today.day) < (birth.month, birth.day))


def _active_plan(session: Session, user: User) -> Optional[TrainingPlan]:
    return session.exec(
        select(TrainingPlan).where(TrainingPlan.user_id == user.id, TrainingPlan.status == "active")
        .order_by(TrainingPlan.created_at.desc())).first()


def _load_context(session: Session, user: User):
    """Build the (profile_dict, goal_dict, metrics_summary) tuple for prompts."""
    p = session.exec(select(Profile).where(Profile.user_id == user.id)).first()
    metrics = [{"date": m.date, "weight_kg": m.weight_kg}
               for m in session.exec(select(BodyMetric).where(BodyMetric.user_id == user.id)).all()]
    weight = next((m["weight_kg"] for m in sorted(metrics, key=lambda x: x["date"], reverse=True)
                   if m["weight_kg"] is not None), None)
    goal_row = session.exec(
        select(Goal).where(Goal.user_id == user.id, Goal.status == "active")
        .order_by(Goal.created_at.desc())).first()
    goal = ({"type": goal_row.type, "target_value": goal_row.target_value,
             "baseline_value": goal_row.baseline_value, "notes": goal_row.notes}
            if goal_row else None)
    workouts = [{"date": w.date, "status": w.status}
                for w in session.exec(select(WorkoutLog).where(WorkoutLog.user_id == user.id)).all()]
    summary = build_context_summary(goal, metrics, workouts, CONTEXT_WINDOW_DAYS, date.today())
    profile = {
        "sex": p.sex, "age": _age(p.birth_date), "height_cm": p.height_cm, "weight": weight,
        "activity_level": p.activity_level, "days_per_week": p.days_per_week,
        "session_length_min": p.session_length_min, "equipment": p.equipment,
        "medical_conditions": p.medical_conditions, "preferences": p.preferences,
    }
    return p, profile, goal, summary


def _prompt_partial(request: Request, prompt: str, notice: str = None):
    return templates.TemplateResponse("partials/_prompt_result.html",
                                      {"request": request, "prompt": prompt, "notice": notice})


def _materialize(session: Session, user: User, plan: TrainingPlan, proposal: dict) -> None:
    plan.plan_json = proposal
    plan.status = "active"
    for s in proposal.get("sessions", []):
        session.add(PlannedSession(
            user_id=user.id, plan_id=plan.id, week_index=s.get("week", 1),
            day_index=s.get("day", 1), title=s.get("title", ""), focus=s.get("focus"),
            exercises_json=s.get("exercises", [])))
    session.add(plan)


@router.get("/plan", response_class=HTMLResponse)
def plan_page(request: Request, session: Session = Depends(get_session),
              user: User = Depends(current_user)):
    plan = _active_plan(session, user)
    sessions = []
    if plan:
        sessions = session.exec(
            select(PlannedSession).where(PlannedSession.plan_id == plan.id)
            .order_by(PlannedSession.week_index, PlannedSession.day_index)).all()
    return templates.TemplateResponse("plan.html", {
        "request": request, "user": user, "plan": plan, "sessions": sessions})


@router.post("/plan/generate", response_class=HTMLResponse)
def generate(request: Request, session: Session = Depends(get_session),
             user: User = Depends(current_user), n_weeks: int = Form(4)):
    p, profile, goal, summary = _load_context(session, user)
    prompt = pb.build_plan(profile, goal, summary, {"n_weeks": n_weeks})
    if not (llm_client.is_configured() and p.use_llm_directly):
        return _prompt_partial(request, prompt)
    try:
        parsed = rp.parse_plan_response(llm_client.complete(prompt))
    except (llm_client.LLMError, rp.ParseError):
        return _prompt_partial(request, prompt, FALLBACK_NOTICE)
    plan = TrainingPlan(user_id=user.id, params_json={"n_weeks": n_weeks},
                        proposals_json=[pl.model_dump() for pl in parsed.plans], status="proposed")
    session.add(plan); session.commit(); session.refresh(plan)
    return templates.TemplateResponse("partials/_plan_proposals.html",
                                      {"request": request, "plan": plan, "plans": plan.proposals_json})


@router.post("/plan/{plan_id}/regenerate", response_class=HTMLResponse)
def regenerate(plan_id: int, request: Request, session: Session = Depends(get_session),
               user: User = Depends(current_user)):
    plan = session.get(TrainingPlan, plan_id)
    if not plan or plan.user_id != user.id:
        return RedirectResponse("/plan", status_code=303)
    p, profile, goal, summary = _load_context(session, user)
    exclude = [pl.get("label") for pl in plan.proposals_json]
    prompt = pb.build_plan(profile, goal, summary, plan.params_json, exclude=exclude)
    if not (llm_client.is_configured() and p.use_llm_directly):
        return _prompt_partial(request, prompt)
    try:
        parsed = rp.parse_plan_response(llm_client.complete(prompt))
    except (llm_client.LLMError, rp.ParseError):
        return templates.TemplateResponse("partials/_plan_proposals.html",
                                          {"request": request, "plan": plan, "plans": plan.proposals_json,
                                           "notice": FALLBACK_NOTICE})
    plan.proposals_json = [pl.model_dump() for pl in parsed.plans]
    session.add(plan); session.commit(); session.refresh(plan)
    return templates.TemplateResponse("partials/_plan_proposals.html",
                                      {"request": request, "plan": plan, "plans": plan.proposals_json})


@router.post("/plan/parse", response_class=HTMLResponse)
def parse_pasted(request: Request, session: Session = Depends(get_session),
                 user: User = Depends(current_user), raw: str = Form(...), n_weeks: int = Form(4)):
    try:
        parsed = rp.parse_plan_response(raw)
    except rp.ParseError as exc:
        return templates.TemplateResponse("partials/_parse_error.html",
                                          {"request": request, "message": str(exc)})
    plan = TrainingPlan(user_id=user.id, params_json={"n_weeks": n_weeks},
                        proposals_json=[pl.model_dump() for pl in parsed.plans], status="proposed")
    session.add(plan); session.commit(); session.refresh(plan)
    return templates.TemplateResponse("partials/_plan_proposals.html",
                                      {"request": request, "plan": plan, "plans": plan.proposals_json})


@router.post("/plan/{plan_id}/activate")
def activate(plan_id: int, session: Session = Depends(get_session),
             user: User = Depends(current_user), choice: int = Form(0)):
    plan = session.get(TrainingPlan, plan_id)
    if not plan or plan.user_id != user.id:
        return RedirectResponse("/plan", status_code=303)
    for other in session.exec(
            select(TrainingPlan).where(TrainingPlan.user_id == user.id,
                                       TrainingPlan.status == "active")).all():
        other.status = "superseded"; session.add(other)
    _materialize(session, user, plan, plan.proposals_json[choice])
    session.commit()
    return RedirectResponse("/plan", status_code=303)


@router.post("/plan/adapt")
def adapt(request: Request, session: Session = Depends(get_session),
          user: User = Depends(current_user), feedback: str = Form("")):
    current = _active_plan(session, user)
    if current is None:
        return Response(status_code=204, headers={"HX-Redirect": "/plan"})
    p, profile, goal, summary = _load_context(session, user)
    prompt = pb.build_adapt(profile, goal, summary, feedback, current.plan_json)
    if not (llm_client.is_configured() and p.use_llm_directly):
        return _prompt_partial(request, prompt)
    try:
        parsed = rp.parse_adapted_plan_response(llm_client.complete(prompt))
    except (llm_client.LLMError, rp.ParseError):
        return _prompt_partial(request, prompt, FALLBACK_NOTICE)
    current.status = "superseded"; session.add(current)
    new_plan = TrainingPlan(user_id=user.id, params_json=current.params_json,
                            proposals_json=[parsed.plan.model_dump()], status="proposed")
    session.add(new_plan); session.commit(); session.refresh(new_plan)
    _materialize(session, user, new_plan, parsed.plan.model_dump())
    session.commit()
    return Response(status_code=204, headers={"HX-Redirect": "/plan"})
