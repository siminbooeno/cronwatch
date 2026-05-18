"""Tests for cronwatch.job_status."""
from __future__ import annotations

import json
import os
import pytest
from datetime import datetime, timezone
from unittest.mock import patch

from cronwatch.config import JobConfig, CronwatchConfig, AlertConfig
from cronwatch.history import JobHistory
from cronwatch.job_status import (
    get_job_status,
    get_all_statuses,
    format_status_table,
    JobStatus,
)


@pytest.fixture()
def history_dir(tmp_path):
    return str(tmp_path / "history")


def _make_job(name: str) -> JobConfig:
    return JobConfig(name=name, command=f"echo {name}", interval_seconds=3600)


def _make_config(*names: str) -> CronwatchConfig:
    alert = AlertConfig()
    return CronwatchConfig(jobs=[_make_job(n) for n in names], alert=alert)


def _add_record(history_dir: str, job_name: str, success: bool) -> None:
    os.makedirs(history_dir, exist_ok=True)
    path = os.path.join(history_dir, f"{job_name}.jsonl")
    ts = datetime.now(timezone.utc).isoformat()
    record = {"timestamp": ts, "success": success, "duration": 1.0}
    with open(path, "a") as fh:
        fh.write(json.dumps(record) + "\n")


# --- get_job_status ---

def test_get_job_status_no_history_returns_unknown(history_dir):
    job = _make_job("backup")
    status = get_job_status(job, history_dir)
    assert status.status == "unknown"
    assert status.total_runs == 0
    assert status.success_rate == -1.0
    assert status.consecutive_failures == 0


def test_get_job_status_all_success_returns_healthy(history_dir):
    job = _make_job("backup")
    for _ in range(3):
        _add_record(history_dir, "backup", success=True)
    status = get_job_status(job, history_dir)
    assert status.status == "healthy"
    assert status.total_runs == 3
    assert status.success_rate == pytest.approx(1.0)
    assert status.consecutive_failures == 0


def test_get_job_status_recent_failure_returns_failing(history_dir):
    job = _make_job("sync")
    _add_record(history_dir, "sync", success=True)
    _add_record(history_dir, "sync", success=False)
    status = get_job_status(job, history_dir)
    assert status.status == "failing"
    assert status.consecutive_failures >= 1


# --- get_all_statuses ---

def test_get_all_statuses_returns_one_per_job(history_dir):
    cfg = _make_config("job_a", "job_b", "job_c")
    results = get_all_statuses(cfg, history_dir)
    assert len(results) == 3
    names = {r.job_name for r in results}
    assert names == {"job_a", "job_b", "job_c"}


def test_get_all_statuses_empty_config(history_dir):
    cfg = _make_config()
    results = get_all_statuses(cfg, history_dir)
    assert results == []


# --- format_status_table ---

def test_format_status_table_empty():
    out = format_status_table([])
    assert "No jobs" in out


def test_format_status_table_contains_job_name(history_dir):
    cfg = _make_config("my_job")
    statuses = get_all_statuses(cfg, history_dir)
    table = format_status_table(statuses)
    assert "my_job" in table
    assert "unknown" in table


def test_format_status_table_healthy_job(history_dir):
    job = _make_job("healthy_job")
    for _ in range(5):
        _add_record(history_dir, "healthy_job", success=True)
    status = get_job_status(job, history_dir)
    table = format_status_table([status])
    assert "healthy" in table
    assert "100.0%" in table
