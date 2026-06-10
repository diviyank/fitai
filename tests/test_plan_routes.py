import json
from sqlmodel import select
from app.models import TrainingPlan, PlannedSession, BodyMetric, Profile, WorkoutLog
from app import llm_client
from datetime import date


def _prep_profile(session, user):
    p = session.exec(select(Profile).where(Profile.user_id == user.id)).first()
    p.birth_date = date(1990, 1, 1); p.height_cm = 180
    session.add(p)
    session.add(BodyMetric(user_id=user.id, date=date.today(), weight_kg=80))
    session.commit()


THREE_PLANS = json.dumps({"plans": [
    {"label": f"Plan {x}", "sessions": [
        {"week": 1, "day": 1, "title": "Haut du corps", "focus": "poussée",
         "exercises": [{"name": "Développé couché", "sets": 4, "reps": "8-12"}]}]}
    for x in ["A", "B", "C"]]})


def test_generate_stores_proposals(authed, session, user, fake_llm):
    _prep_profile(session, user)
    fake_llm["reply"] = THREE_PLANS
    r = authed.post("/plan/generate", data={"n_weeks": "4"})
    assert r.status_code == 200 and fake_llm["calls"] == 1
    plan = session.exec(select(TrainingPlan).where(TrainingPlan.user_id == user.id)).first()
    assert len(plan.proposals_json) == 3 and plan.status == "proposed"


def test_activate_materializes_sessions(authed, session, user, fake_llm):
    _prep_profile(session, user)
    fake_llm["reply"] = THREE_PLANS
    authed.post("/plan/generate", data={"n_weeks": "4"})
    plan = session.exec(select(TrainingPlan).where(TrainingPlan.user_id == user.id)).first()
    authed.post(f"/plan/{plan.id}/activate", data={"choice": "1"})
    session.refresh(plan)
    assert plan.status == "active"
    sessions = session.exec(select(PlannedSession).where(PlannedSession.plan_id == plan.id)).all()
    assert len(sessions) == 1 and sessions[0].title == "Haut du corps"


def test_generate_falls_back_to_prompt_when_disabled(authed, session, user):
    _prep_profile(session, user)
    p = session.exec(select(Profile).where(Profile.user_id == user.id)).first()
    p.use_llm_directly = False; session.add(p); session.commit()
    r = authed.post("/plan/generate", data={"n_weeks": "4"})
    assert r.status_code == 200 and "```" in r.text   # copy-paste prompt shown


def test_adapt_supersedes_and_creates_new_active(authed, session, user, fake_llm):
    _prep_profile(session, user)
    fake_llm["reply"] = THREE_PLANS
    authed.post("/plan/generate", data={"n_weeks": "4"})
    plan = session.exec(select(TrainingPlan).where(TrainingPlan.user_id == user.id)).first()
    authed.post(f"/plan/{plan.id}/activate", data={"choice": "0"})
    fake_llm["reply"] = json.dumps({"plan": {"label": "Adapté", "sessions": [
        {"week": 1, "day": 1, "title": "Bas du corps", "exercises": []}]}})
    authed.post("/plan/adapt", data={"feedback": "le genou tire"})
    plans = session.exec(select(TrainingPlan).where(TrainingPlan.user_id == user.id)
                         .order_by(TrainingPlan.created_at)).all()
    statuses = [p.status for p in plans]
    assert "superseded" in statuses
    active = [p for p in plans if p.status == "active"]
    assert len(active) == 1 and active[0].plan_json["label"] == "Adapté"
