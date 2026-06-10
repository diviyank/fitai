"""PURE progress math: trends, streaks, adherence, goal progress. No DB, no web."""
from datetime import date
from typing import Optional


def moving_average(values: list[float], window: int) -> Optional[float]:
    vals = [v for v in values if v is not None]
    if not vals:
        return None
    window = min(window, len(vals))
    tail = vals[-window:]
    return sum(tail) / len(tail)


def _weights_sorted(metrics: list[dict]) -> list[dict]:
    return sorted([m for m in metrics if m.get("weight_kg") is not None], key=lambda m: m["date"])


def weight_trend(metrics: list[dict], window: int = 7) -> dict:
    """current weight, moving average, and delta across the available window."""
    series = _weights_sorted(metrics)
    if not series:
        return {"current": None, "average": None, "delta": None}
    weights = [m["weight_kg"] for m in series]
    current = weights[-1]
    earliest = weights[-min(window, len(weights))] if len(weights) > 1 else weights[0]
    return {
        "current": current,
        "average": moving_average(weights, window),
        "delta": current - earliest,
    }


def goal_progress(baseline: float, current: float, target: float) -> float:
    """Percent of the way from baseline to target (clamped 0..100)."""
    span = target - baseline
    if span == 0:
        return 100.0
    pct = (current - baseline) / span * 100.0
    return max(0.0, min(100.0, pct))


def adherence(done: int, planned: int) -> float:
    if planned <= 0:
        return 0.0
    return done / planned


def streak(dates: list[date], today: date) -> int:
    """Consecutive days ending today that have at least one logged date."""
    have = set(dates)
    count, cursor = 0, today
    while cursor in have:
        count += 1
        cursor = date.fromordinal(cursor.toordinal() - 1)
    return count
