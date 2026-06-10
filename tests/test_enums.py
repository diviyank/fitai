from app import enums


def test_activity_multipliers_cover_levels():
    assert set(enums.ACTIVITY_LEVELS) == set(enums.ACTIVITY_MULTIPLIERS)
    assert enums.ACTIVITY_MULTIPLIERS["sedentaire"] == 1.2
    assert "lose_weight" in enums.GOAL_TYPES
    assert "dejeuner" in enums.MEAL_SLOTS
