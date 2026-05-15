"""Tests for cronwatch.thresholds."""
from __future__ import annotations

import os
import pytest

from cronwatch.thresholds import (
    ThresholdPolicy,
    ThresholdViolation,
    check_thresholds,
    check_all_thresholds,
    parse_threshold_policies,
)
from cronwatch.history import JobHistory
from cronwatch.config import CronwatchConfig, JobConfig, AlertConfig


@pytest.fixture()
def history_dir(tmp_path):
    d = tmp_path / "history"
    d.mkdir()
    return str(d)


def _make_job(name: str = "backup") -> JobConfig:
    return JobConfig(name=name, command="echo hi", interval_seconds=3600)


def _make_config(*names: str) -> CronwatchConfig:
    alert = AlertConfig()
    jobs = [_make_job(n) for n in names]
    return CronwatchConfig(jobs=jobs, alert=alert)


def _add_records(history_dir: str, job_name: str, outcomes: list[bool]) -> None:
    hist = JobHistory(history_dir, job_name)
    for success in outcomes:
        if success:
            hist.add(success=True, duration=1.0)
        else:
            hist.add(success=False, duration=1.0)


def test_no_violation_all_success(history_dir):
    job = _make_job()
    _add_records(history_dir, job.name, [True] * 10)
    result = check_thresholds(job, history_dir)
    assert result is None


def test_warn_on_consecutive_failures(history_dir):
    job = _make_job()
    _add_records(history_dir, job.name, [True] * 5 + [False, False])
    policy = ThresholdPolicy(warn_consecutive=2, crit_consecutive=5)
    result = check_thresholds(job, history_dir, policy)
    assert result is not None
    assert result.level == "warn"
    assert result.job_name == job.name
    assert result.consecutive_failures == 2


def test_crit_on_high_failure_rate(history_dir):
    job = _make_job()
    _add_records(history_dir, job.name, [False] * 12 + [True] * 8)
    policy = ThresholdPolicy(warn_failure_rate=0.2, crit_failure_rate=0.5)
    result = check_thresholds(job, history_dir, policy)
    assert result is not None
    assert result.level == "crit"
    assert result.failure_rate >= 0.5


def test_no_history_no_violation(history_dir):
    job = _make_job()
    result = check_thresholds(job, history_dir)
    assert result is None


def test_check_all_thresholds_returns_violations(history_dir):
    cfg = _make_config("job_a", "job_b")
    _add_records(history_dir, "job_a", [False] * 10)
    _add_records(history_dir, "job_b", [True] * 10)
    violations = check_all_thresholds(cfg, history_dir)
    names = [v.job_name for v in violations]
    assert "job_a" in names
    assert "job_b" not in names


def test_parse_threshold_policies_returns_defaults(history_dir):
    cfg = _make_config("alpha", "beta")
    policies = parse_threshold_policies(cfg)
    assert "alpha" in policies
    assert "beta" in policies
    assert policies["alpha"].warn_consecutive == 2


def test_violation_fields(history_dir):
    job = _make_job("myjob")
    _add_records(history_dir, job.name, [False, False, False, False, False])
    policy = ThresholdPolicy(crit_consecutive=5)
    result = check_thresholds(job, history_dir, policy)
    assert result is not None
    assert result.job_name == "myjob"
    assert "consecutive" in result.reason
