from datetime import date, timedelta
from app import progress


def test_moving_average():
    assert progress.moving_average([2, 4, 6], 3) == 4
    assert progress.moving_average([], 3) is None


def test_weight_trend_delta_over_window():
    today = date(2026, 6, 10)
    metrics = [
        {"date": today - timedelta(days=7), "weight_kg": 79.0},
        {"date": today - timedelta(days=3), "weight_kg": 78.6},
        {"date": today, "weight_kg": 78.4},
    ]
    trend = progress.weight_trend(metrics)
    assert trend["current"] == 78.4
    assert round(trend["delta"], 1) == -0.6  # latest minus earliest in window


def test_goal_progress_percent():
    # lose 6 kg: from 84 baseline toward 78 target, now at 79.8 → 70%
    pct = progress.goal_progress(baseline=84.0, current=79.8, target=78.0)
    assert round(pct) == 70


def test_goal_progress_handles_no_movement_target():
    assert progress.goal_progress(baseline=80, current=80, target=80) == 100


def test_adherence_ratio():
    assert progress.adherence(done=3, planned=4) == 0.75
    assert progress.adherence(done=0, planned=0) == 0.0


def test_streak_counts_consecutive_days_to_today():
    today = date(2026, 6, 10)
    dates = [today, today - timedelta(days=1), today - timedelta(days=2), today - timedelta(days=5)]
    assert progress.streak(dates, today=today) == 3
