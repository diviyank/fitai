# Internal keys are stable identifiers; user-facing labels come from i18n.

SEXES = ["homme", "femme"]

# Mifflin-St Jeor TDEE activity multipliers.
ACTIVITY_MULTIPLIERS = {
    "sedentaire": 1.2,
    "leger": 1.375,
    "modere": 1.55,
    "actif": 1.725,
    "tres_actif": 1.9,
}
ACTIVITY_LEVELS = list(ACTIVITY_MULTIPLIERS)

GOAL_TYPES = ["lose_weight", "gain_muscle", "endurance", "general", "custom"]

MEAL_SLOTS = ["petit_dejeuner", "dejeuner", "diner", "collation"]

WORKOUT_STATUS = ["done", "skipped", "partial"]

UNITS = ["metric"]
