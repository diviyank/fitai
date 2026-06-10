import json
from sqlmodel import select
from app.models import FoodLog
from app import response_parser as rp, llm_client


def test_manual_add_makes_no_api_call(authed, session, user, fake_llm):
    r = authed.post("/nutrition/add", data={
        "description": "poulet riz", "meal_slot": "dejeuner",
        "calories": "500", "protein_g": "40", "carbs_g": "50", "fat_g": "12"})
    assert r.status_code in (200, 303)
    row = session.exec(select(FoodLog).where(FoodLog.user_id == user.id)).first()
    assert row.calories == 500 and row.source == "manual"
    assert fake_llm["calls"] == 0


def test_batched_estimate_one_call_fills_all(authed, session, user, fake_llm):
    authed.post("/nutrition/add", data={"description": "poulet riz", "meal_slot": "dejeuner",
                                        "calories": "", "protein_g": "", "carbs_g": "", "fat_g": ""})
    authed.post("/nutrition/add", data={"description": "yaourt", "meal_slot": "collation",
                                        "calories": "", "protein_g": "", "carbs_g": "", "fat_g": ""})
    fake_llm["reply"] = json.dumps({"items": [
        {"description": "poulet riz", "calories": 520, "protein_g": 38, "carbs_g": 55, "fat_g": 14},
        {"description": "yaourt", "calories": 90, "protein_g": 5, "carbs_g": 7, "fat_g": 4}]})
    authed.post("/nutrition/estimate")
    rows = session.exec(select(FoodLog).where(FoodLog.user_id == user.id)).all()
    assert fake_llm["calls"] == 1                      # single batched call
    assert sorted(r.calories for r in rows) == [90, 520]
    assert all(r.source == "llm" for r in rows)


def test_estimate_falls_back_to_prompt_on_error(authed, fake_llm):
    authed.post("/nutrition/add", data={"description": "soupe", "meal_slot": "diner",
                                        "calories": "", "protein_g": "", "carbs_g": "", "fat_g": ""})
    fake_llm["reply"] = llm_client.LLMError("boom")
    r = authed.post("/nutrition/estimate")
    assert r.status_code == 200
    assert "indisponible" in r.text.lower() or "```" in r.text  # copy-paste prompt shown
