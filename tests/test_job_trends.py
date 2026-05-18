"""Tests for cronwatch.job_trends."""
from __future__ import annotations

import json
from pathlib import Path

import pytest

from cronwatch.history import JobHistory
from cronwatch.job_trends import (
    TrendStats,
    _detect_trend,
    compute_trend,
    compute_all_trends,
)


@pytest.fixture()
def history_dir(tmp_path: Path) -> Path:
    d = tmp_path / "history"
    d.mkdir()
    return d


def _add(history_dir: Path, job: str, duration: float, success: bool = True):
    jh = JobHistory(job, history_dir)
    jh.add(
        success=success,
        duration_seconds=duration,
        exit_code=0 if success else 1,
        output="",
    )


def _make_job(name: str):
    class _J:
        pass
    j = _J()
    j.name = name
    return j


def _make_config(names):
    class _C:
        pass
    c = _C()
    c.jobs = [_make_job(n) for n in names]
    return c


# --- _detect_trend ---

def test_detect_trend_unknown_too_few():
    assert _detect_trend([1.0, 2.0, 3.0], window=5) == "unknown"


def test_detect_trend_stable():
    data = [1.0] * 20
    assert _detect_trend(data, window=5) == "stable"


def test_detect_trend_degrading():
    # Early samples are fast, recent ones are slow
    data = [1.0] * 15 + [3.0] * 5
    result = _detect_trend(data, window=5)
    assert result == "degrading"


def test_detect_trend_improving():
    # Early samples are slow, recent ones are fast
    data = [3.0] * 15 + [0.5] * 5
    result = _detect_trend(data, window=5)
    assert result == "improving"


# --- compute_trend ---

def test_compute_trend_no_history(history_dir):
    stats = compute_trend("missing_job", history_dir)
    assert stats.job_name == "missing_job"
    assert stats.mean_duration is None
    assert stats.trend == "unknown"


def test_compute_trend_single_record(history_dir):
    _add(history_dir, "job_a", 2.5)
    stats = compute_trend("job_a", history_dir)
    assert stats.sample_count == 1
    assert stats.mean_duration == pytest.approx(2.5)
    assert stats.min_duration == pytest.approx(2.5)
    assert stats.max_duration == pytest.approx(2.5)
    assert stats.stdev_duration == pytest.approx(0.0)


def test_compute_trend_multiple_records(history_dir):
    for d in [1.0, 2.0, 3.0, 4.0, 5.0]:
        _add(history_dir, "job_b", d)
    stats = compute_trend("job_b", history_dir)
    assert stats.sample_count == 5
    assert stats.mean_duration == pytest.approx(3.0)
    assert stats.median_duration == pytest.approx(3.0)
    assert stats.min_duration == pytest.approx(1.0)
    assert stats.max_duration == pytest.approx(5.0)


def test_compute_trend_as_dict_keys(history_dir):
    _add(history_dir, "job_c", 1.0)
    d = compute_trend("job_c", history_dir).as_dict()
    assert set(d.keys()) == {"job", "samples", "mean_s", "median_s", "stdev_s", "min_s", "max_s", "trend"}


def test_compute_trend_as_text_no_data(history_dir):
    text = compute_trend("nope", history_dir).as_text()
    assert "no duration data" in text


def test_compute_trend_as_text_with_data(history_dir):
    _add(history_dir, "job_d", 5.0)
    text = compute_trend("job_d", history_dir).as_text()
    assert "job_d" in text
    assert "mean=" in text


# --- compute_all_trends ---

def test_compute_all_trends_returns_one_per_job(history_dir):
    cfg = _make_config(["a", "b", "c"])
    results = compute_all_trends(cfg, history_dir)
    assert len(results) == 3
    assert {r.job_name for r in results} == {"a", "b", "c"}
