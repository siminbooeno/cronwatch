"""Tests for cronwatch.pauses."""

from __future__ import annotations

import json
from datetime import datetime, timezone, timedelta
from pathlib import Path
from unittest.mock import patch

import pytest

from cronwatch.pauses import (
    pause_job,
    resume_job,
    is_paused,
    get_pause_record,
    list_paused_jobs,
)

FAKE_NOW = datetime(2024, 6, 1, 12, 0, 0, tzinfo=timezone.utc)


@pytest.fixture()
def state_dir(tmp_path: Path) -> str:
    return str(tmp_path)


def test_pause_creates_file(state_dir):
    pause_job(state_dir, "backup")
    assert (Path(state_dir) / "pauses" / "backup.json").exists()


def test_pause_record_fields(state_dir):
    with patch("cronwatch.pauses._utcnow", return_value=FAKE_NOW):
        record = pause_job(state_dir, "backup", reason="maintenance")
    assert record["job"] == "backup"
    assert record["reason"] == "maintenance"
    assert record["until"] is None
    assert record["paused_at"] == FAKE_NOW.isoformat()


def test_pause_with_until(state_dir):
    until = FAKE_NOW + timedelta(hours=2)
    record = pause_job(state_dir, "backup", until=until)
    assert record["until"] == until.isoformat()


def test_is_paused_indefinite(state_dir):
    pause_job(state_dir, "backup")
    assert is_paused(state_dir, "backup") is True


def test_is_paused_not_paused(state_dir):
    assert is_paused(state_dir, "backup") is False


def test_is_paused_future_expiry(state_dir):
    future = FAKE_NOW + timedelta(hours=1)
    with patch("cronwatch.pauses._utcnow", return_value=FAKE_NOW):
        pause_job(state_dir, "backup", until=future)
        assert is_paused(state_dir, "backup") is True


def test_is_paused_expired_removes_file(state_dir):
    past = FAKE_NOW - timedelta(hours=1)
    pause_job(state_dir, "backup", until=past)
    assert is_paused(state_dir, "backup") is False
    assert not (Path(state_dir) / "pauses" / "backup.json").exists()


def test_resume_returns_true_when_paused(state_dir):
    pause_job(state_dir, "backup")
    assert resume_job(state_dir, "backup") is True
    assert not (Path(state_dir) / "pauses" / "backup.json").exists()


def test_resume_returns_false_when_not_paused(state_dir):
    assert resume_job(state_dir, "backup") is False


def test_get_pause_record_returns_dict(state_dir):
    pause_job(state_dir, "backup", reason="test")
    record = get_pause_record(state_dir, "backup")
    assert record is not None
    assert record["reason"] == "test"


def test_get_pause_record_none_when_not_paused(state_dir):
    assert get_pause_record(state_dir, "backup") is None


def test_list_paused_jobs_empty(state_dir):
    assert list_paused_jobs(state_dir) == []


def test_list_paused_jobs_multiple(state_dir):
    pause_job(state_dir, "alpha")
    pause_job(state_dir, "beta")
    records = list_paused_jobs(state_dir)
    names = {r["job"] for r in records}
    assert names == {"alpha", "beta"}


def test_list_paused_jobs_excludes_expired(state_dir):
    past = FAKE_NOW - timedelta(minutes=5)
    pause_job(state_dir, "expired", until=past)
    pause_job(state_dir, "active")
    records = list_paused_jobs(state_dir)
    assert all(r["job"] == "active" for r in records)
