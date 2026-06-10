from app import prompt_builder as pb

PROFILE = {
    "sex": "homme", "age": 30, "height_cm": 180, "weight": 80, "activity_level": "modere",
    "days_per_week": 4, "session_length_min": 45, "equipment": "haltères, barre",
    "medical_conditions": "genou fragile", "preferences": "pas de course",
}
GOAL = {"type": "gain_muscle", "target_value": 84, "notes": "prise de masse"}


def test_base_context_includes_profile_and_goal():
    ctx = pb.base_context(PROFILE, GOAL, "résumé de progression")
    for needle in ["homme", "180", "haltères", "genou fragile", "gain_muscle", "résumé de progression"]:
        assert needle in ctx


def test_build_plan_requests_three_json_plans_and_uses_constraints():
    prompt = pb.build_plan(PROFILE, GOAL, "résumé", {"n_weeks": 4})
    assert "4" in prompt                      # days/week or weeks present
    assert "plans" in prompt and "sessions" in prompt
    assert "json" in prompt.lower()
    assert "3" in prompt or "trois" in prompt.lower()


def test_build_plan_exclude_clause():
    prompt = pb.build_plan(PROFILE, GOAL, "résumé", {"n_weeks": 4}, exclude=["Plan A", "Plan B"])
    assert "Plan A" in prompt


def test_build_adapt_includes_feedback_and_current_plan_and_one_plan_schema():
    current = {"label": "Actuel", "sessions": [{"week": 1, "day": 1, "title": "Haut"}]}
    prompt = pb.build_adapt(PROFILE, GOAL, "résumé progression", "le genou tire", current)
    assert "le genou tire" in prompt
    assert "Actuel" in prompt or "Haut" in prompt
    assert '"plan"' in prompt              # single adapted plan schema
