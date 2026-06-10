"""PURE nutrition math: Mifflin-St Jeor BMR, TDEE, goal-adjusted calorie & macro targets.
No DB, no web. Activity multipliers live in enums."""
from typing import Optional
from .enums import ACTIVITY_MULTIPLIERS

GOAL_CALORIE_ADJUSTMENT = {
    "lose_weight": -500,
    "gain_muscle": +300,
    "endurance": 0,
    "general": 0,
    "custom": 0,
}
PROTEIN_G_PER_KG = 1.8
FAT_FRACTION_OF_CALORIES = 0.25


def mifflin_st_jeor(sex: str, age: int, height_cm: float, weight_kg: float) -> float:
    base = 10 * weight_kg + 6.25 * height_cm - 5 * age
    return base + 5 if sex == "homme" else base - 161


def tdee(bmr: float, activity_level: str) -> float:
    return bmr * ACTIVITY_MULTIPLIERS.get(activity_level, 1.2)


def compute_targets(sex: str, age: int, height_cm: float, weight_kg: float,
                    activity_level: str, goal_type: Optional[str] = None,
                    calorie_override: Optional[int] = None) -> dict:
    bmr = mifflin_st_jeor(sex, age, height_cm, weight_kg)
    maintenance = tdee(bmr, activity_level)
    if calorie_override is not None:
        calories = int(calorie_override)
    else:
        calories = round(maintenance) + GOAL_CALORIE_ADJUSTMENT.get(goal_type, 0)
    protein_g = round(PROTEIN_G_PER_KG * weight_kg)
    fat_g = round(FAT_FRACTION_OF_CALORIES * calories / 9)
    carbs_g = round((calories - protein_g * 4 - fat_g * 9) / 4)
    return {
        "bmr": round(bmr), "tdee": round(maintenance), "calories": calories,
        "protein_g": protein_g, "carbs_g": max(carbs_g, 0), "fat_g": fat_g,
    }
