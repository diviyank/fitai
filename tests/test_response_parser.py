import pytest
from app import response_parser as rp


def test_extract_json_from_fenced_block():
    text = 'Voici:\n```json\n{"items": [{"description": "riz", "calories": 200}]}\n```\nmerci'
    data = rp.extract_json_block(text)
    assert data["items"][0]["description"] == "riz"


def test_parse_nutrition_list():
    text = '{"items": [{"description": "poulet", "calories": 250, "protein_g": 30, "carbs_g": 0, "fat_g": 12}]}'
    parsed = rp.parse_nutrition_list_response(text)
    assert parsed.items[0].calories == 250 and parsed.items[0].protein_g == 30


def test_parse_nutrition_empty_raises():
    with pytest.raises(rp.ParseError):
        rp.parse_nutrition_list_response('{"items": []}')


def test_garbage_raises_parse_error():
    with pytest.raises(rp.ParseError):
        rp.parse_nutrition_list_response("pas de json ici")
