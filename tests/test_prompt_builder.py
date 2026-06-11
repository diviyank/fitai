from app import prompt_builder as pb


def test_nutrition_prompt_lists_foods_and_requests_json():
    prompt = pb.build_nutrition_estimate(["poulet riz brocoli", "yaourt"])
    assert "poulet riz brocoli" in prompt and "yaourt" in prompt
    assert "json" in prompt.lower() and "items" in prompt
    assert "calories" in prompt


def test_exclude_clause_appends_names():
    assert "Plan A" in pb._exclude_clause(["Plan A", "Plan B"])
    assert pb._exclude_clause([]) == ""


def test_with_clarifying_questions_prepends_invitation_without_losing_original():
    base = pb.build_nutrition_estimate(["poulet riz brocoli", "yaourt"])
    wrapped = pb.with_clarifying_questions(base)
    assert base in wrapped                       # original prompt preserved intact
    assert wrapped != base
    assert "question" in wrapped.lower()         # invites clarifying questions
    assert wrapped.index("Avant de répondre") < wrapped.index(base[:30])  # clause first
