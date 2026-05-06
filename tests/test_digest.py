"""Tests for cronwatch.digest."""

from __future__ import annotations

import json
import os
from datetime import datetime, timezone
from pathlib import Path

import pytest

from cronwatch.config import JobConfig, AlertConfig, CronwatchConfig
from cronwatch.digest import build_digest, DigestReport, JobSummary
from cronwatch.history import JobHistory
from cronwatch.state import record_success, record_failure


@pytest.fixture()
def dirs(tmp_path: Path):
    history_dir = str(tmp_path / "history")
    state_dir = str(tmp_path / "state")
    os.makedirs(history_dir, exist_ok=True)
    os.makedirs(state_dir, exist_ok=True)
    return history_dir, state_dir


def _make_config(*names: str) -> CronwatchConfig:
    jobs = [JobConfig(name=n, command="echo hi", interval=300) for n in names]
    alert = AlertConfig()
    return CronwatchConfig(jobs=jobs, alert=alert)


def test_digest_no_history(dirs):
    history_dir, state_dir = dirs
    config = _make_config("backup")
    report = build_digest(config, history_dir, state_dir)

    assert isinstance(report, DigestReport)
    assert len(report.jobs) == 1
    summary = report.jobs[0]
    assert summary.name == "backup"
    assert summary.total_runs == 0
    assert summary.success_rate == 0.0
    assert summary.consecutive_failures == 0
    assert summary.last_seen is None


def test_digest_all_success(dirs):
    history_dir, state_dir = dirs
    config = _make_config("nightly")
    h = JobHistory(history_dir, "nightly")
    h.add(success=True, duration=1.0)
    h.add(success=True, duration=1.2)
    record_success(state_dir, "nightly")

    report = build_digest(config, history_dir, state_dir)
    summary = report.jobs[0]

    assert summary.total_runs == 2
    assert summary.success_rate == 1.0
    assert summary.consecutive_failures == 0
    assert summary.last_seen is not None


def test_digest_consecutive_failures(dirs):
    history_dir, state_dir = dirs
    config = _make_config("sync")
    h = JobHistory(history_dir, "sync")
    h.add(success=True, duration=0.5)
    h.add(success=False, duration=0.1)
    h.add(success=False, duration=0.1)

    report = build_digest(config, history_dir, state_dir)
    summary = report.jobs[0]

    assert summary.consecutive_failures == 2
    assert pytest.approx(summary.success_rate) == 1 / 3


def test_digest_healthy_unhealthy_counts(dirs):
    history_dir, state_dir = dirs
    config = _make_config("jobA", "jobB", "jobC")

    JobHistory(history_dir, "jobA").add(success=True, duration=1.0)
    JobHistory(history_dir, "jobB").add(success=False, duration=0.5)
    # jobC has no history

    report = build_digest(config, history_dir, state_dir)
    assert report.healthy_count == 2  # jobA and jobC (0 consec failures)
    assert report.unhealthy_count == 1


def test_digest_as_text_contains_job_name(dirs):
    history_dir, state_dir = dirs
    config = _make_config("my-job")
    report = build_digest(config, history_dir, state_dir)
    text = report.as_text()
    assert "my-job" in text
    assert "CronWatch Digest" in text
