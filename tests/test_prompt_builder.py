from app import prompt_builder as pb


def test_nutrition_prompt_lists_foods_and_requests_json():
    prompt = pb.build_nutrition_estimate(["poulet riz brocoli", "yaourt"])
    assert "poulet riz brocoli" in prompt and "yaourt" in prompt
    assert "json" in prompt.lower() and "items" in prompt
    assert "calories" in prompt


def test_exclude_clause_appends_names():
    assert "Plan A" in pb._exclude_clause(["Plan A", "Plan B"])
    assert pb._exclude_clause([]) == ""
