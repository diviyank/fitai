"""Per-kind extra template context for panels (reroll targets, form defaults).
Pure-ish view helper: dict in, dict out."""


def extra_context(kind: str, params: dict, result: dict | None) -> dict:
    """Return per-kind template context. Placeholder for fitai's per-kind context wiring."""
    return {}
