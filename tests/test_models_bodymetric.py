from datetime import date
from app.models import BodyMetric


def test_bodymetric_optional_fields():
    m = BodyMetric(user_id=1, date=date(2026, 6, 10))
    assert m.weight_kg is None and m.steps is None
    m2 = BodyMetric(user_id=1, date=date(2026, 6, 10), weight_kg=78.4, steps=7240, energy=4)
    assert m2.weight_kg == 78.4 and m2.energy == 4
