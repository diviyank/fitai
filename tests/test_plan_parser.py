import pytest
from app import response_parser as rp


PLAN_JSON = '''```json
{"plans": [
  {"label": "Plan A", "sessions": [
    {"week": 1, "day": 1, "title": "Haut du corps", "focus": "poussée",
     "exercises": [{"name": "Développé couché", "sets": 4, "reps": "8-12", "rest": "90s"}]}
  ]}
]}
```'''


def test_parse_plan_response():
    parsed = rp.parse_plan_response(PLAN_JSON)
    assert parsed.plans[0].label == "Plan A"
    assert parsed.plans[0].sessions[0].exercises[0].name == "Développé couché"
    assert parsed.plans[0].sessions[0].exercises[0].sets == 4


def test_parse_plan_empty_raises():
    with pytest.raises(rp.ParseError):
        rp.parse_plan_response('{"plans": []}')


def test_parse_adapted_plan():
    text = '{"plan": {"label": "Adapté", "sessions": [{"week": 1, "day": 1, "title": "Bas du corps"}]}}'
    parsed = rp.parse_adapted_plan_response(text)
    assert parsed.plan.label == "Adapté" and parsed.plan.sessions[0].title == "Bas du corps"
