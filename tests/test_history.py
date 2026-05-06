"""Tests for cronwatch.history module."""

import json
import pytest
from pathlib import Path

from cronwatch.history import (
    ExecutionRecord,
    JobHistory,
    append_execution,
    load_history,
    save_history,
    MAX_HISTORY_ENTRIES,
)


@pytest.fixture
def tmp_history_dir(tmp_path):
    return str(tmp_path / "history")


def test_job_history_defaults():
    h = JobHistory(job_name="backup")
    assert h.records == []
    assert h.success_rate() is None
    assert h.last_success() is None
    assert h.last_failure() is None
    assert h.consecutive_failures() == 0


def test_success_rate_all_success():
    h = JobHistory(job_name="job")
    for _ in range(4):
        h.add(ExecutionRecord(timestamp="2024-01-01T00:00:00+00:00", success=True))
    assert h.success_rate() == 1.0


def test_success_rate_mixed():
    h = JobHistory(job_name="job")
    h.add(ExecutionRecord(timestamp="2024-01-01T00:00:00+00:00", success=True))
    h.add(ExecutionRecord(timestamp="2024-01-01T01:00:00+00:00", success=False))
    assert h.success_rate() == 0.5


def test_consecutive_failures():
    h = JobHistory(job_name="job")
    h.add(ExecutionRecord(timestamp="t1", success=True))
    h.add(ExecutionRecord(timestamp="t2", success=False))
    h.add(ExecutionRecord(timestamp="t3", success=False))
    assert h.consecutive_failures() == 2


def test_consecutive_failures_none_after_success():
    h = JobHistory(job_name="job")
    h.add(ExecutionRecord(timestamp="t1", success=False))
    h.add(ExecutionRecord(timestamp="t2", success=True))
    assert h.consecutive_failures() == 0


def test_history_capped_at_max_entries():
    h = JobHistory(job_name="job")
    for i in range(MAX_HISTORY_ENTRIES + 20):
        h.add(ExecutionRecord(timestamp=f"t{i}", success=True))
    assert len(h.records) == MAX_HISTORY_ENTRIES


def test_save_and_load_history(tmp_history_dir):
    h = JobHistory(job_name="my_job")
    h.add(ExecutionRecord(timestamp="2024-01-01T00:00:00+00:00", success=True, exit_code=0, duration_seconds=1.5))
    save_history(tmp_history_dir, h)
    loaded = load_history(tmp_history_dir, "my_job")
    assert len(loaded.records) == 1
    assert loaded.records[0].success is True
    assert loaded.records[0].exit_code == 0
    assert loaded.records[0].duration_seconds == 1.5


def test_load_history_missing_file(tmp_history_dir):
    h = load_history(tmp_history_dir, "nonexistent")
    assert h.job_name == "nonexistent"
    assert h.records == []


def test_append_execution_creates_record(tmp_history_dir):
    h = append_execution(tmp_history_dir, "deploy", success=True, exit_code=0, duration_seconds=2.3)
    assert len(h.records) == 1
    assert h.records[0].success is True


def test_append_execution_accumulates(tmp_history_dir):
    append_execution(tmp_history_dir, "deploy", success=True)
    append_execution(tmp_history_dir, "deploy", success=False, note="timeout")
    h = load_history(tmp_history_dir, "deploy")
    assert len(h.records) == 2
    assert h.last_failure().note == "timeout"


def test_history_file_safe_name(tmp_history_dir):
    append_execution(tmp_history_dir, "my/job name", success=True)
    p = Path(tmp_history_dir) / "my_job_name.history.json"
    assert p.exists()
