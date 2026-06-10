from app.models import Goal


def test_goal_defaults():
    g = Goal(user_id=1, type="lose_weight")
    assert g.status == "active" and g.target_value is None
