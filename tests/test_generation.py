from app import generation, llm_client


def test_kind_llm_has_expected_ceilings():
    assert generation.KIND_LLM["plan"]["max_tokens"] == 4000
    assert generation.KIND_LLM["plan"]["effort"] == "medium"
    assert generation.KIND_LLM["plan_adapt"]["max_tokens"] == 4000
    assert generation.KIND_LLM["plan_adapt"]["effort"] == "medium"


def test_nutrition_uses_haiku_with_no_thinking():
    assert generation.KIND_LLM["nutrition"]["model"] == "claude-haiku-4-5"
    assert generation.KIND_LLM["nutrition"]["max_tokens"] == 1500
    assert generation.KIND_LLM["nutrition"]["thinking"] is None


def test_llm_kwargs_nutrition_omits_thinking_and_effort():
    kw = generation._llm_kwargs("nutrition", None)
    assert kw.get("thinking") is None
    assert "effort" not in kw
    assert kw["model"] == "claude-haiku-4-5"


def test_llm_kwargs_plan_includes_effort():
    kw = generation._llm_kwargs("plan", None)
    assert kw["effort"] == "medium"
    assert kw["max_tokens"] == 4000


def test_llm_kwargs_with_system_adds_cached_block():
    kw = generation._llm_kwargs("plan", "BASE CONTEXT")
    assert kw["system"] == [
        {"type": "text", "text": "BASE CONTEXT", "cache_control": {"type": "ephemeral"}}]


def test_llm_kwargs_without_system_omits_it():
    kw = generation._llm_kwargs("plan", None)
    assert "system" not in kw
