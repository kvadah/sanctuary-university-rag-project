"""Unit tests for the analytics reducers (pure functions, no DB or services)."""
import datetime as dt

from app.services.analytics_service import (
    _as_utc_date,
    _latency_stats,
    _percentile,
    _token_stats,
    _volume_by_day,
)


def test_percentile_empty_is_none():
    assert _percentile([], 50) is None
    assert _percentile([], 95) is None


def test_percentile_single_value():
    assert _percentile([42.0], 50) == 42.0
    assert _percentile([42.0], 95) == 42.0


def test_percentile_nearest_rank():
    values = [10, 20, 30, 40, 50, 60, 70, 80, 90, 100]
    assert _percentile(values, 50) == 50.0   # ceil(0.50*10)=5th value
    assert _percentile(values, 95) == 100.0  # ceil(0.95*10)=10th value
    assert _percentile(values, 100) == 100.0
    assert _percentile(values, 0) == 10.0    # rank clamps to 1st value


def test_percentile_sorts_input():
    assert _percentile([30, 10, 20], 50) == 20.0


def test_latency_stats_empty():
    s = _latency_stats([])
    assert s.sample_count == 0
    assert s.avg is None and s.p50 is None and s.p95 is None


def test_latency_stats_skips_missing_and_non_numeric():
    metas = [
        {"latency_ms": 100},
        {"latency_ms": 300},
        {},                      # missing key -> skipped
        {"latency_ms": None},    # None -> skipped
        {"latency_ms": "oops"},  # wrong type -> skipped
    ]
    s = _latency_stats(metas)
    assert s.sample_count == 2
    assert s.avg == 200.0
    assert s.p50 == 100.0   # nearest-rank on [100, 300]
    assert s.p95 == 300.0


def test_token_stats_sums_and_skips_none():
    metas = [
        {"prompt_tokens": 10, "completion_tokens": 5, "total_tokens": 15},
        {"prompt_tokens": 20, "completion_tokens": None, "total_tokens": 20},
        {},  # nothing usable
    ]
    s = _token_stats(metas)
    assert s.prompt == 30
    assert s.completion == 5
    assert s.total == 35


def test_token_stats_empty():
    s = _token_stats([])
    assert (s.prompt, s.completion, s.total) == (0, 0, 0)


def test_as_utc_date_handles_naive_and_aware():
    aware = dt.datetime(2026, 8, 26, 23, 30, tzinfo=dt.timezone.utc)
    naive = dt.datetime(2026, 8, 26, 23, 30)
    assert _as_utc_date(aware) == dt.date(2026, 8, 26)
    assert _as_utc_date(naive) == dt.date(2026, 8, 26)


def test_volume_by_day_buckets_and_fills_gaps():
    # Anchor at noon UTC so ±minutes never straddles a day boundary.
    today = dt.datetime.now(dt.timezone.utc).date()
    noon = dt.datetime.combine(today, dt.time(12, 0), tzinfo=dt.timezone.utc)
    since = noon - dt.timedelta(days=3)
    created = [noon, noon - dt.timedelta(minutes=5), noon - dt.timedelta(days=2)]

    out = _volume_by_day(created, since)
    dates = [d for d, _ in out]
    counts = dict(out)

    # Ascending and continuous from since's day through today (inclusive).
    assert dates == sorted(dates)
    assert dates[0] == since.date().isoformat()
    assert dates[-1] == today.isoformat()
    # Two on today, one two days ago, and a gap day filled with 0.
    assert counts[today.isoformat()] == 2
    assert counts[(noon - dt.timedelta(days=2)).date().isoformat()] == 1
    assert counts[since.date().isoformat()] == 0
    assert sum(counts.values()) == 3


def test_volume_by_day_empty():
    now = dt.datetime.now(dt.timezone.utc)
    since = now - dt.timedelta(days=2)
    out = _volume_by_day([], since)
    assert out and all(c == 0 for _, c in out)
    assert len(out) >= 3  # since's day .. today, inclusive
