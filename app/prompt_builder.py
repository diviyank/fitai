"""PURE prompt-building functions. No DB, no web. All output is French."""

import json as _json

NUTRITION_JSON_SCHEMA = (
    '{\n'
    '  "items": [\n'
    '    {"description": "...", "calories": 0, "protein_g": 0, "carbs_g": 0, "fat_g": 0}\n'
    '  ]\n'
    '}'
)


def _exclude_clause(exclude) -> str:
    """Optional 'do not repeat these' line appended to one-shot prompts (re-roll)."""
    names = [n for n in (exclude or []) if n and n.strip()]
    if not names:
        return ""
    return f"\nNe propose pas à nouveau : {', '.join(names)}.\n"


def build_nutrition_estimate(foods: list[str]) -> str:
    listing = "\n".join(f"- {f}" for f in foods if f and f.strip())
    return (
        "Tu es un nutritionniste. Estime les valeurs nutritionnelles de chaque aliment "
        "ou repas listé ci-dessous (portion telle que décrite). Sois réaliste.\n\n"
        f"## Aliments\n{listing}\n\n"
        "## Format de réponse OBLIGATOIRE\n"
        "Réponds avec un seul bloc ```json``` respectant EXACTEMENT ce schéma, "
        "avec une entrée par aliment dans le même ordre, calories en kcal, macros en grammes :\n"
        f"```json\n{NUTRITION_JSON_SCHEMA}\n```"
    )


PLAN_JSON_SCHEMA = (
    '{\n'
    '  "plans": [\n'
    '    {\n'
    '      "label": "Plan A",\n'
    '      "sessions": [\n'
    '        {"week": 1, "day": 1, "title": "...", "focus": "...",\n'
    '         "exercises": [{"name": "...", "sets": 4, "reps": "8-12", "target_weight": "ou null", "rest": "90s", "notes": null}]}\n'
    '      ]\n'
    '    }\n'
    '  ]\n'
    '}'
)

ADAPT_JSON_SCHEMA = (
    '{\n'
    '  "plan": {\n'
    '    "label": "...",\n'
    '    "sessions": [\n'
    '      {"week": 1, "day": 1, "title": "...", "focus": "...",\n'
    '       "exercises": [{"name": "...", "sets": 4, "reps": "8-12", "target_weight": "ou null", "rest": "90s", "notes": null}]}\n'
    '    ]\n'
    '  }\n'
    '}'
)


def base_context(profile: dict, goal: dict | None, metrics_summary: str) -> str:
    goal_line = "aucun objectif défini"
    if goal:
        target = f", cible {goal.get('target_value')}" if goal.get("target_value") else ""
        goal_line = f"{goal.get('type')}{target} — {goal.get('notes') or ''}".strip(" —")
    return (
        "## Profil\n"
        f"- Sexe : {profile.get('sex')}\n"
        f"- Âge : {profile.get('age')}\n"
        f"- Taille : {profile.get('height_cm')} cm\n"
        f"- Poids : {profile.get('weight')} kg\n"
        f"- Niveau d'activité : {profile.get('activity_level')}\n"
        f"- Séances/semaine souhaitées : {profile.get('days_per_week')}\n"
        f"- Durée par séance : {profile.get('session_length_min')} min\n"
        f"- Équipement : {profile.get('equipment') or 'aucun précisé'}\n"
        f"- Conditions / blessures : {profile.get('medical_conditions') or 'aucune'}\n"
        f"- Préférences : {profile.get('preferences') or 'aucune'}\n"
        f"## Objectif\n- {goal_line}\n"
        f"## Progression récente\n{metrics_summary or 'aucune donnée'}\n"
    )


def build_plan(profile: dict, goal: dict | None, metrics_summary: str,
               params: dict, exclude=None) -> str:
    n_weeks = params.get("n_weeks", 4)
    return (
        "Tu es un coach sportif. Conçois un programme d'entraînement personnalisé.\n\n"
        + base_context(profile, goal, metrics_summary)
        + f"\n## Contraintes\n- Durée du programme : {n_weeks} semaines\n"
        f"- Respecte l'équipement, les blessures et le nombre de séances par semaine.\n"
        + _exclude_clause(exclude)
        + "\n## Format de réponse OBLIGATOIRE\n"
        "Réponds avec un seul bloc ```json``` proposant EXACTEMENT 3 programmes "
        "(3 entrées dans \"plans\"), respectant ce schéma :\n"
        f"```json\n{PLAN_JSON_SCHEMA}\n```"
    )


def build_adapt(profile: dict, goal: dict | None, metrics_summary: str,
                feedback: str, current_plan: dict, exclude=None) -> str:
    return (
        "Tu es un coach sportif. Adapte le programme ci-dessous selon le retour de l'utilisateur "
        "et sa progression. Garde ce qui marche, ajuste le reste.\n\n"
        + base_context(profile, goal, metrics_summary)
        + f"\n## Programme actuel\n```json\n{_json.dumps(current_plan, ensure_ascii=False)}\n```\n"
        f"\n## Retour de l'utilisateur\n{feedback or '(aucun retour particulier)'}\n"
        + _exclude_clause(exclude)
        + "\n## Format de réponse OBLIGATOIRE\n"
        "Réponds avec un seul bloc ```json``` contenant UN programme adapté, "
        "respectant ce schéma :\n"
        f"```json\n{ADAPT_JSON_SCHEMA}\n```"
    )
