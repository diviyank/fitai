"""Per-kind generation wiring: LLM config, work() builders, and result rendering.
The only module that maps a `kind` to its model/tokens/thinking and result partial."""
from . import llm_client

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
