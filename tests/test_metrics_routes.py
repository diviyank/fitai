from datetime import date
from sqlmodel import select
from app.models import BodyMetric


def test_quick_add_creates_today_row(authed, session, user, fake_llm):
    r = authed.post("/metrics/quick", data={"weight_kg": "78.4", "steps": "7240", "energy": "4"})
    assert r.status_code in (200, 303)
    row = session.exec(select(BodyMetric).where(BodyMetric.user_id == user.id)).first()
    assert row.weight_kg == 78.4 and row.steps == 7240 and row.date == date.today()
    assert fake_llm["calls"] == 0  # cost guard: data entry never calls the API


def test_quick_add_upserts_same_day(authed, session, user):
    authed.post("/metrics/quick", data={"weight_kg": "78.4", "steps": "", "energy": ""})
    authed.post("/metrics/quick", data={"weight_kg": "", "steps": "8000", "energy": ""})
    rows = session.exec(select(BodyMetric).where(BodyMetric.user_id == user.id)).all()
    assert len(rows) == 1
    assert rows[0].weight_kg == 78.4 and rows[0].steps == 8000


def test_metrics_page_lists_history(authed):
    authed.post("/metrics/quick", data={"weight_kg": "80", "steps": "", "energy": ""})
    r = authed.get("/metrics")
    assert r.status_code == 200 and "80" in r.text


def test_metrics_isolated_between_users(authed, client, session):
    from app import auth
    authed.post("/metrics/quick", data={"weight_kg": "70", "steps": "", "energy": ""})
    other = auth.create_user(session, "mallory", "pw")
    token = auth.create_session(session, other)
    client.cookies.set(auth.COOKIE_NAME, token)
    r = client.get("/metrics")
    assert "70" not in r.text  # cannot see tester's data
