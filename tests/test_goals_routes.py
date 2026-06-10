from sqlmodel import select
from app.models import Goal


def test_create_goal_and_list(authed, session, user):
    r = authed.post("/goals/add", data={
        "type": "lose_weight", "target_value": "78", "target_date": "2026-09-01",
        "baseline_value": "84", "notes": "été"}, follow_redirects=False)
    assert r.status_code == 303
    g = session.exec(select(Goal).where(Goal.user_id == user.id)).first()
    assert g.type == "lose_weight" and g.target_value == 78 and g.baseline_value == 84
    page = authed.get("/goals")
    assert "lose_weight" in page.text or "78" in page.text


def test_retire_goal(authed, session, user):
    authed.post("/goals/add", data={"type": "general", "target_value": "", "target_date": "",
                                     "baseline_value": "", "notes": ""})
    g = session.exec(select(Goal).where(Goal.user_id == user.id)).first()
    authed.post(f"/goals/{g.id}/retire", data={"status": "achieved"})
    session.refresh(g)
    assert g.status == "achieved"
