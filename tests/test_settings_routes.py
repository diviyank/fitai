from sqlmodel import select
from app.models import Profile


def test_settings_page_renders(authed):
    r = authed.get("/settings")
    assert r.status_code == 200
    assert "Réglages" in r.text
    assert "use_llm_directly" in r.text


def test_settings_post_updates_profile(authed, session, user):
    authed.post("/settings", data={
        "sex": "femme", "birth_date": "1990-05-01", "height_cm": "170",
        "activity_level": "actif", "language": "fr",
        "medical_conditions": "genou fragile", "preferences": "",
        "equipment": "haltères, barre", "days_per_week": "4", "session_length_min": "60",
        "calorie_target_override": "", "use_llm_directly": "on"})
    p = session.exec(select(Profile).where(Profile.user_id == user.id)).first()
    assert p.sex == "femme" and p.height_cm == 170 and p.days_per_week == 4
    assert p.use_llm_directly is True


def test_settings_post_toggle_off(authed, session, user):
    authed.post("/settings", data={
        "sex": "homme", "birth_date": "", "height_cm": "",
        "activity_level": "modere", "language": "fr",
        "medical_conditions": "", "preferences": "", "equipment": "",
        "days_per_week": "3", "session_length_min": "45", "calorie_target_override": ""})
    p = session.exec(select(Profile).where(Profile.user_id == user.id)).first()
    assert p.use_llm_directly is False
