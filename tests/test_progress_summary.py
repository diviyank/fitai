from datetime import date, timedelta
from app import progress


def test_summary_is_bounded_and_mentions_key_facts():
    today = date(2026, 6, 10)
    # 100 days of weight logs — summary must NOT embed them all
    metrics = [{"date": today - timedelta(days=i), "weight_kg": 80 - i * 0.05} for i in range(100)]
    workouts = [{"date": today - timedelta(days=i), "status": "done"} for i in range(0, 6, 2)]
    summary = progress.build_context_summary(
        goal={"type": "lose_weight", "baseline_value": 84, "target_value": 78},
        metrics=metrics, workout_logs=workouts, window_days=14, today=today)
    assert isinstance(summary, str)
    assert "kg" in summary
    assert summary.count("\n") < 15            # compact, not a data dump
    assert "lose_weight" in summary or "objectif" in summary.lower()
