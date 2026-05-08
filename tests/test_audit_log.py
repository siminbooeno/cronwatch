"""Tests for cronwatch.audit_log."""

from __future__ import annotations

import json
from datetime import datetime, timedelta, timezone
from pathlib import Path
from unittest.mock import patch

import pytest

from cronwatch.audit_log import append_event, read_events, prune_audit_log, AUDIT_LOG_FILENAME


@pytest.fixture()
def state_dir(tmp_path: Path) -> str:
    return str(tmp_path / "state")


def test_append_creates_file(state_dir: str) -> None:
    append_event(state_dir, "alert_sent", job_name="backup")
    log = Path(state_dir) / AUDIT_LOG_FILENAME
    assert log.exists()


def test_append_writes_valid_json(state_dir: str) -> None:
    append_event(state_dir, "job_run", job_name="sync", details={"exit_code": 0})
    log = Path(state_dir) / AUDIT_LOG_FILENAME
    record = json.loads(log.read_text().strip())
    assert record["event"] == "job_run"
    assert record["job"] == "sync"
    assert record["details"]["exit_code"] == 0
    assert "ts" in record


def test_append_multiple_events(state_dir: str) -> None:
    append_event(state_dir, "alert_sent", job_name="a")
    append_event(state_dir, "alert_sent", job_name="b")
    events = read_events(state_dir)
    assert len(events) == 2


def test_read_events_empty_when_no_file(state_dir: str) -> None:
    result = read_events(state_dir)
    assert result == []


def test_read_events_filter_by_event_type(state_dir: str) -> None:
    append_event(state_dir, "alert_sent", job_name="a")
    append_event(state_dir, "job_run", job_name="b")
    result = read_events(state_dir, event_type="alert_sent")
    assert len(result) == 1
    assert result[0]["job"] == "a"


def test_read_events_filter_by_job_name(state_dir: str) -> None:
    append_event(state_dir, "alert_sent", job_name="backup")
    append_event(state_dir, "alert_sent", job_name="sync")
    result = read_events(state_dir, job_name="backup")
    assert len(result) == 1
    assert result[0]["job"] == "backup"


def test_read_events_limit(state_dir: str) -> None:
    for i in range(5):
        append_event(state_dir, "job_run", job_name=f"job_{i}")
    result = read_events(state_dir, limit=2)
    assert len(result) == 2
    assert result[-1]["job"] == "job_4"


def test_event_without_job_name(state_dir: str) -> None:
    append_event(state_dir, "startup")
    events = read_events(state_dir)
    assert len(events) == 1
    assert "job" not in events[0]


def test_prune_removes_old_entries(state_dir: str) -> None:
    old_ts = (datetime.now(timezone.utc) - timedelta(days=40)).isoformat()
    new_ts = datetime.now(timezone.utc).isoformat()

    log_path = Path(state_dir) / AUDIT_LOG_FILENAME
    log_path.parent.mkdir(parents=True, exist_ok=True)
    with open(log_path, "w") as fh:
        fh.write(json.dumps({"ts": old_ts, "event": "old_event"}) + "\n")
        fh.write(json.dumps({"ts": new_ts, "event": "new_event"}) + "\n")

    removed = prune_audit_log(state_dir, keep_days=30)
    assert removed == 1
    remaining = read_events(state_dir)
    assert len(remaining) == 1
    assert remaining[0]["event"] == "new_event"


def test_prune_returns_zero_when_no_file(state_dir: str) -> None:
    assert prune_audit_log(state_dir) == 0
