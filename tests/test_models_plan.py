from datetime import date
from app.models import TrainingPlan, PlannedSession, WorkoutLog


def test_plan_and_session_defaults():
    p = TrainingPlan(user_id=1)
    assert p.status == "proposed" and p.proposals_json == []
    s = PlannedSession(user_id=1, plan_id=1, week_index=1, day_index=1, title="Haut du corps")
    assert s.focus is None and s.exercises_json == []


def test_workoutlog_defaults():
    w = WorkoutLog(user_id=1, date=date(2026, 6, 10), status="done")
    assert w.planned_session_id is None and w.performed_json == [] and w.feeling == ""
