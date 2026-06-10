"""PURE prompt-building functions. No DB, no web. All output is French."""

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
