"""Per-kind generation wiring: LLM config, work() builders, and result rendering.
The only module that maps a `kind` to its model/tokens/thinking and result partial."""
from . import llm_client
from . import response_parser as rp

# Per-kind complete() kwargs. Haiku 4.5: no adaptive thinking, and effort is unsupported (would 400).
KIND_LLM = {
    "plan": {"max_tokens": 4000, "effort": "medium"},
    "plan_adapt": {"max_tokens": 4000, "effort": "medium"},
    "nutrition": {"model": "claude-haiku-4-5", "max_tokens": 1500, "thinking": None},
}


def _llm_kwargs(kind: str, system: str | None) -> dict:
    """Per-kind complete() kwargs, optionally with the stable base context sent as a
    cached system block. Caching is best-effort: Sonnet 4.6 only caches prefixes above
    ~2048 tokens, so for small base contexts this is a silent no-op (verify via
    usage.cache_read_input_tokens). It never changes the produced output."""
    kw = dict(KIND_LLM[kind])
    if system:
        kw["system"] = [{"type": "text", "text": system,
                         "cache_control": {"type": "ephemeral"}}]
    return kw


def build_plan_work(*, json_prompt: str, params: dict, user_id: int):
    """Build a work() function for plan generation that stores proposals and returns plan_id."""
    cfg = KIND_LLM["plan"]

    def work() -> dict:
        parsed = rp.parse_plan_response(llm_client.complete(json_prompt, **cfg))
        from sqlmodel import Session
        from .db import get_engine
        from .models import TrainingPlan
        with Session(get_engine()) as s:
            plan = TrainingPlan(
                user_id=user_id,
                params_json=params,
                proposals_json=[p.model_dump() for p in parsed.plans],
                status="proposed")
            s.add(plan)
            s.commit()
            s.refresh(plan)
            return {"plan_id": plan.id}

    return work
