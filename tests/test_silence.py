"""Tests for cronwatch.silence module."""

from datetime import datetime, timezone, time

import pytest

from cronwatch.silence import (
    SilenceWindow,
    _parse_time,
    parse_silence_window,
    is_silenced,
    active_windows,
)


# ---------------------------------------------------------------------------
# _parse_time
# ---------------------------------------------------------------------------

def test_parse_time_valid():
    assert _parse_time("08:30") == time(8, 30)


def test_parse_time_single_digit_hour():
    assert _parse_time("9:05") == time(9, 5)


def test_parse_time_invalid_raises():
    with pytest.raises(ValueError):
        _parse_time("25:00")

    with pytest.raises(ValueError):
        _parse_time("not-a-time")


# ---------------------------------------------------------------------------
# parse_silence_window
# ---------------------------------------------------------------------------

def test_parse_silence_window_minimal():
    raw = {"job": "backup", "start": "02:00", "end": "04:00"}
    w = parse_silence_window(raw)
    assert w.job_name == "backup"
    assert w.start == time(2, 0)
    assert w.end == time(4, 0)
    assert w.days == list(range(7))
    assert w.reason == ""


def test_parse_silence_window_with_days_and_reason():
    raw = {"job": "deploy", "start": "22:00", "end": "23:59", "days": [5, 6], "reason": "weekend maintenance"}
    w = parse_silence_window(raw)
    assert w.days == [5, 6]
    assert w.reason == "weekend maintenance"


# ---------------------------------------------------------------------------
# is_silenced
# ---------------------------------------------------------------------------

def _dt(hour: int, minute: int, weekday: int = 0) -> datetime:
    """Build a UTC datetime with the given time; weekday 0=Monday."""
    # Use a known Monday: 2024-01-01 is a Monday
    from datetime import timedelta
    base = datetime(2024, 1, 1, hour, minute, tzinfo=timezone.utc)  # Monday
    return base + timedelta(days=weekday)


def test_not_silenced_when_no_windows():
    assert is_silenced("myjob", [], now=_dt(10, 0)) is False


def test_not_silenced_different_job():
    w = SilenceWindow(job_name="other", start=time(0, 0), end=time(23, 59))
    assert is_silenced("myjob", [w], now=_dt(12, 0)) is False


def test_silenced_within_window():
    w = SilenceWindow(job_name="myjob", start=time(2, 0), end=time(4, 0))
    assert is_silenced("myjob", [w], now=_dt(3, 0)) is True


def test_not_silenced_outside_window():
    w = SilenceWindow(job_name="myjob", start=time(2, 0), end=time(4, 0))
    assert is_silenced("myjob", [w], now=_dt(5, 0)) is False


def test_silenced_midnight_wrap():
    # Window 23:00 – 01:00 wraps midnight
    w = SilenceWindow(job_name="myjob", start=time(23, 0), end=time(1, 0))
    assert is_silenced("myjob", [w], now=_dt(23, 30)) is True
    assert is_silenced("myjob", [w], now=_dt(0, 30)) is True
    assert is_silenced("myjob", [w], now=_dt(2, 0)) is False


def test_silenced_respects_days():
    # Only Saturday (5) and Sunday (6)
    w = SilenceWindow(job_name="myjob", start=time(0, 0), end=time(23, 59), days=[5, 6])
    assert is_silenced("myjob", [w], now=_dt(12, 0, weekday=0)) is False  # Monday
    assert is_silenced("myjob", [w], now=_dt(12, 0, weekday=5)) is True   # Saturday


# ---------------------------------------------------------------------------
# active_windows
# ---------------------------------------------------------------------------

def test_active_windows_filters_by_job():
    w1 = SilenceWindow(job_name="job-a", start=time(1, 0), end=time(2, 0))
    w2 = SilenceWindow(job_name="job-b", start=time(3, 0), end=time(4, 0))
    w3 = SilenceWindow(job_name="job-a", start=time(5, 0), end=time(6, 0))
    result = active_windows("job-a", [w1, w2, w3])
    assert result == [w1, w3]


def test_active_windows_empty_when_none_match():
    w = SilenceWindow(job_name="other", start=time(0, 0), end=time(1, 0))
    assert active_windows("myjob", [w]) == []
