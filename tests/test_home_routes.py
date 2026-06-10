import json
from datetime import date
from sqlmodel import select
from app.models import TrainingPlan, Profile, BodyMetric


def test_dashboard_shows_session_and_weight(authed, session, user, fake_llm):
    p = session.exec(select(Profile).where(Profile.user_id == user.id)).first()
    p.birth_date = date(1990, 1, 1); p.height_cm = 180; session.add(p)
    session.add(BodyMetric(user_id=user.id, date=date.today(), weight_kg=78.4)); session.commit()
    fake_llm["reply"] = json.dumps({"plans": [
        {"label": f"Plan {x}", "sessions": [
            {"week": 1, "day": 1, "title": "Haut du corps", "focus": "poussée", "exercises": []},
            {"week": 1, "day": 7, "title": "Bas du corps", "focus": "jambes", "exercises": []}]}
        for x in "ABC"]})
    authed.post("/plan/generate", data={"n_weeks": "4"})
    plan = session.exec(select(TrainingPlan).where(TrainingPlan.user_id == user.id)).first()
    authed.post(f"/plan/{plan.id}/activate", data={"choice": "0"})
    r = authed.get("/")
    assert r.status_code == 200
    assert "78.4" in r.text or "78,4" in r.text       # weight tile
    assert "Haut du corps" in r.text or "Bas du corps" in r.text  # a session card


def test_dashboard_works_with_no_plan_or_metrics(authed):
    r = authed.get("/")
    assert r.status_code == 200          # empty-state, no crash
