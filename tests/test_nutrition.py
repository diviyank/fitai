import pytest
from app import nutrition


def test_mifflin_st_jeor_male_and_female():
    # male: 10*80 + 6.25*180 - 5*30 + 5 = 1780
    assert nutrition.mifflin_st_jeor("homme", 30, 180, 80) == pytest.approx(1780)
    # female: 10*60 + 6.25*165 - 5*30 - 161 = 1320.25
    assert nutrition.mifflin_st_jeor("femme", 30, 165, 60) == pytest.approx(1320.25)


def test_tdee_applies_activity_multiplier():
    assert nutrition.tdee(1780, "modere") == pytest.approx(1780 * 1.55)


def test_targets_apply_goal_deficit_and_protein():
    t = nutrition.compute_targets("homme", 30, 180, 80, "modere", goal_type="lose_weight")
    assert t["calories"] == round(1780 * 1.55) - 500
    assert t["protein_g"] == round(1.8 * 80)
    # macros sum back to calories (within rounding)
    kcal = t["protein_g"] * 4 + t["carbs_g"] * 4 + t["fat_g"] * 9
    assert abs(kcal - t["calories"]) <= 12


def test_targets_surplus_for_muscle():
    base = nutrition.compute_targets("homme", 30, 180, 80, "modere", goal_type="general")["calories"]
    gain = nutrition.compute_targets("homme", 30, 180, 80, "modere", goal_type="gain_muscle")["calories"]
    assert gain == base + 300


def test_calorie_override_short_circuits():
    t = nutrition.compute_targets("homme", 30, 180, 80, "modere", goal_type="lose_weight", calorie_override=2000)
    assert t["calories"] == 2000
