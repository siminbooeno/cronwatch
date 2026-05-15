"""Tests for cronwatch.job_timeout."""

from __future__ import annotations

import json
import os
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any, Dict

import pytest

from cronwatch.job_timeout import (
    TimeoutViolation,
    check_timeouts,
    format_violation,
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _iso(dt: datetime) -> str:
    return dt.isoformat()


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


class _FakeJob:
    """Minimal stand-in for JobConfig."""

    def __init__(self, name: str, timeout: Any = None):
        self.name = name
        self.raw: Dict[str, Any] = {}
        if timeout is not None:
            self.raw["timeout"] = timeout


def _write_record(history_dir: str, job_name: str, record: dict) -> None:
    job_dir = Path(history_dir) / job_name
    job_dir.mkdir(parents=True, exist_ok=True)
    records_file = job_dir / "records.jsonl"
    with records_file.open("a") as fh:
        fh.write(json.dumps(record) + "\n")


@pytest.fixture()
def history_dir(tmp_path: Path) -> str:
    return str(tmp_path / "history")


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------

def test_no_timeout_configured_skips_job(history_dir: str) -> None:
    job = _FakeJob("backup")  # no timeout key
    violations = check_timeouts([job], history_dir)
    assert violations == []


def test_no_violations_when_within_timeout(history_dir: str) -> None:
    job = _FakeJob("sync", timeout=60)
    now = _utcnow()
    _write_record(history_dir, "sync", {
        "timestamp": _iso(now - timedelta(minutes=5)),
        "duration_seconds": 30,
        "status": "success",
    })
    violations = check_timeouts([job], history_dir)
    assert violations == []


def test_violation_when_duration_exceeds_timeout(history_dir: str) -> None:
    job = _FakeJob("report", timeout=120)
    now = _utcnow()
    _write_record(history_dir, "report", {
        "timestamp": _iso(now - timedelta(minutes=10)),
        "duration_seconds": 200,
        "status": "success",
    })
    violations = check_timeouts([job], history_dir)
    assert len(violations) == 1
    v = violations[0]
    assert v.job_name == "report"
    assert v.timeout_seconds == 120
    assert v.actual_seconds == 200.0


def test_old_records_outside_window_ignored(history_dir: str) -> None:
    job = _FakeJob("cleanup", timeout=30)
    now = _utcnow()
    _write_record(history_dir, "cleanup", {
        "timestamp": _iso(now - timedelta(hours=3)),
        "duration_seconds": 999,
        "status": "success",
    })
    violations = check_timeouts([job], history_dir, window_seconds=3600)
    assert violations == []


def test_multiple_violations_returned(history_dir: str) -> None:
    job = _FakeJob("etl", timeout=60)
    now = _utcnow()
    for minutes_ago in (5, 15, 25):
        _write_record(history_dir, "etl", {
            "timestamp": _iso(now - timedelta(minutes=minutes_ago)),
            "duration_seconds": 90,
            "status": "success",
        })
    violations = check_timeouts([job], history_dir)
    assert len(violations) == 3


def test_records_missing_duration_skipped(history_dir: str) -> None:
    job = _FakeJob("ping", timeout=10)
    now = _utcnow()
    _write_record(history_dir, "ping", {
        "timestamp": _iso(now - timedelta(minutes=1)),
        "status": "success",
        # no duration_seconds
    })
    violations = check_timeouts([job], history_dir)
    assert violations == []


def test_format_violation_contains_key_info() -> None:
    v = TimeoutViolation(
        job_name="deploy",
        timeout_seconds=300,
        actual_seconds=450.5,
        occurred_at="2024-06-01T12:00:00+00:00",
    )
    msg = format_violation(v)
    assert "deploy" in msg
    assert "450.5" in msg
    assert "300" in msg
