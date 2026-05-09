"""Tests for cronwatch.dedup alert deduplication module."""

from __future__ import annotations

import json
from datetime import datetime, timezone, timedelta
from pathlib import Path
from unittest.mock import patch

import pytest

from cronwatch.dedup import (
    is_duplicate,
    record_alert_dedup,
    clear_dedup,
    _dedup_path,
)


@pytest.fixture()
def state_dir(tmp_path: Path) -> str:
    return str(tmp_path)


def _now() -> datetime:
    return datetime.now(timezone.utc)


def test_not_duplicate_when_no_entry(state_dir):
    assert is_duplicate(state_dir, "backup", "missed", window_seconds=300) is False


def test_record_creates_entry(state_dir):
    record_alert_dedup(state_dir, "backup", "missed")
    data = json.loads(_dedup_path(state_dir).read_text())
    assert "backup::missed" in data


def test_duplicate_within_window(state_dir):
    record_alert_dedup(state_dir, "backup", "missed")
    assert is_duplicate(state_dir, "backup", "missed", window_seconds=300) is True


def test_not_duplicate_after_window_expires(state_dir):
    past = _now() - timedelta(seconds=400)
    data = {"backup::missed": {"last_sent": past.isoformat(), "job": "backup", "event": "missed"}}
    _dedup_path(state_dir).write_text(json.dumps(data))
    assert is_duplicate(state_dir, "backup", "missed", window_seconds=300) is False


def test_different_event_type_not_duplicate(state_dir):
    record_alert_dedup(state_dir, "backup", "missed")
    assert is_duplicate(state_dir, "backup", "failed", window_seconds=300) is False


def test_different_job_not_duplicate(state_dir):
    record_alert_dedup(state_dir, "backup", "missed")
    assert is_duplicate(state_dir, "sync", "missed", window_seconds=300) is False


def test_clear_dedup_specific_event(state_dir):
    record_alert_dedup(state_dir, "backup", "missed")
    record_alert_dedup(state_dir, "backup", "failed")
    clear_dedup(state_dir, "backup", event_type="missed")
    data = json.loads(_dedup_path(state_dir).read_text())
    assert "backup::missed" not in data
    assert "backup::failed" in data


def test_clear_dedup_all_events_for_job(state_dir):
    record_alert_dedup(state_dir, "backup", "missed")
    record_alert_dedup(state_dir, "backup", "failed")
    record_alert_dedup(state_dir, "sync", "missed")
    clear_dedup(state_dir, "backup")
    data = json.loads(_dedup_path(state_dir).read_text())
    assert "backup::missed" not in data
    assert "backup::failed" not in data
    assert "sync::missed" in data


def test_corrupt_dedup_file_treated_as_empty(state_dir):
    _dedup_path(state_dir).write_text("not-json")
    assert is_duplicate(state_dir, "backup", "missed", window_seconds=300) is False


def test_record_overwrites_previous_entry(state_dir):
    past = _now() - timedelta(seconds=400)
    data = {"backup::missed": {"last_sent": past.isoformat(), "job": "backup", "event": "missed"}}
    _dedup_path(state_dir).write_text(json.dumps(data))
    record_alert_dedup(state_dir, "backup", "missed")
    assert is_duplicate(state_dir, "backup", "missed", window_seconds=300) is True
