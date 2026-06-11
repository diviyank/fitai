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
    r = authed.post("/nutrition/estimate")
    # Response should be the panel (status 200) with job running
    assert r.status_code == 200
    assert 'id="panel-nutrition"' in r.text
    # Refresh session to see updates made by the background work
    session.expire_all()
    rows = session.exec(select(FoodLog).where(FoodLog.user_id == user.id)).all()
    assert fake_llm["calls"] == 1                      # single batched call
    assert sorted(row.calories for row in rows if row.calories is not None) == [90, 520]
    assert all(r.source == "llm" for r in rows)


def test_estimate_uses_haiku_with_correct_kwargs(authed, session, user, fake_llm, monkeypatch):
    authed.post("/nutrition/add", data={"description": "poulet riz", "meal_slot": "dejeuner",
                                        "calories": "", "protein_g": "", "carbs_g": "", "fat_g": ""})
    fake_llm["reply"] = json.dumps({"items": [
        {"description": "poulet riz", "calories": 520, "protein_g": 38, "carbs_g": 55, "fat_g": 14}]})

    captured_kw = {}
    original_complete = fake_llm["_original_complete"] if "_original_complete" in fake_llm else None

    def capture_complete(prompt, **kw):
        captured_kw.update(kw)
        return json.dumps({"items": [
            {"description": "poulet riz", "calories": 520, "protein_g": 38, "carbs_g": 55, "fat_g": 14}]})

    monkeypatch.setattr(llm_client, "complete", capture_complete)
    authed.post("/nutrition/estimate")

    # Verify Haiku model and no thinking
    assert captured_kw.get("model") == "claude-haiku-4-5"
    assert "thinking" not in captured_kw or captured_kw.get("thinking") is None


def test_estimate_falls_back_to_prompt_on_error(authed, fake_llm):
    authed.post("/nutrition/add", data={"description": "soupe", "meal_slot": "diner",
                                        "calories": "", "protein_g": "", "carbs_g": "", "fat_g": ""})
    fake_llm["reply"] = llm_client.LLMError("boom")
    r = authed.post("/nutrition/estimate")
    assert r.status_code == 200
    assert "indisponible" in r.text.lower() or "```" in r.text  # copy-paste prompt shown


def test_nutrition_copy_paste_invites_clarifying_questions(authed, session, user):
    from datetime import date
    from app.models import FoodLog
    session.add(FoodLog(user_id=user.id, date=date.today(), description="pomme", source="manual"))
    session.commit()
    r = authed.post("/nutrition/estimate")
    assert r.status_code == 200
    assert "Avant de répondre" in r.text


def test_nutrition_direct_call_prompt_excludes_clarifying_questions(authed, session, user, fake_llm):
    from datetime import date
    from app.models import FoodLog
    session.add(FoodLog(user_id=user.id, date=date.today(), description="pomme", source="manual"))
    session.commit()
    fake_llm["reply"] = json.dumps({"items": [
        {"description": "pomme", "calories": 52, "protein_g": 0, "carbs_g": 14, "fat_g": 0}]})
    authed.post("/nutrition/estimate")
    assert "Avant de répondre" not in fake_llm["prompts"][-1]
