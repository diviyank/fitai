from datetime import date
from app.models import FoodLog


def test_foodlog_defaults():
    f = FoodLog(user_id=1, date=date(2026, 6, 10), description="poulet riz")
    assert f.source == "manual" and f.calories is None
