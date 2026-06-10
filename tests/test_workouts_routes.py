import json
from datetime import date
from sqlmodel import select
from app.models import TrainingPlan, PlannedSession, WorkoutLog, Profile, BodyMetric


def _active_plan_with_session(authed, session, user, fake_llm):
    p = session.exec(select(Profile).where(Profile.user_id == user.id)).first()
    p.birth_date = date(1990, 1, 1); p.height_cm = 180; session.add(p)
    session.add(BodyMetric(user_id=user.id, date=date.today(), weight_kg=80)); session.commit()
    fake_llm["reply"] = json.dumps({"plans": [
        {"label": f"Plan {x}", "sessions": [
            {"week": 1, "day": 1, "title": "Haut du corps", "focus": "poussée",
             "exercises": [{"name": "Développé couché", "sets": 4, "reps": "8-12"}]}]} for x in "ABC"]})
    authed.post("/plan/generate", data={"n_weeks": "4"})
    plan = session.exec(select(TrainingPlan).where(TrainingPlan.user_id == user.id)).first()
    authed.post(f"/plan/{plan.id}/activate", data={"choice": "0"})
    return session.exec(select(PlannedSession).where(PlannedSession.plan_id == plan.id)).first()


def test_session_page_renders_exercises(authed, session, user, fake_llm):
    ps = _active_plan_with_session(authed, session, user, fake_llm)
    r = authed.get(f"/workouts/session/{ps.id}")
    assert r.status_code == 200 and "Développé couché" in r.text


def test_log_workout_makes_no_api_call(authed, session, user, fake_llm):
    ps = _active_plan_with_session(authed, session, user, fake_llm)
    calls_before = fake_llm["calls"]
    r = authed.post("/workouts/log", data={
        "planned_session_id": str(ps.id), "status": "done", "rpe": "8",
        "feeling": "le genou tire", "notes": "RAS"}, follow_redirects=False)
    assert r.status_code == 303
    w = session.exec(select(WorkoutLog).where(WorkoutLog.user_id == user.id)).first()
    assert w.status == "done" and w.feeling == "le genou tire" and w.rpe == 8
    assert fake_llm["calls"] == calls_before  # logging feedback is free


def test_workouts_isolated(authed, client, session, user, fake_llm):
    ps = _active_plan_with_session(authed, session, user, fake_llm)
    from app import auth
    other = auth.create_user(session, "eve", "pw")
    token = auth.create_session(session, other)
    client.cookies.set(auth.COOKIE_NAME, token)
    r = client.get(f"/workouts/session/{ps.id}")
    assert r.status_code in (303, 404) or "Développé couché" not in r.text
