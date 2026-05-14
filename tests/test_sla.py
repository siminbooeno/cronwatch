"""Tests for cronwatch.sla."""
from __future__ import annotations

import os
import pytest

from cronwatch.config import JobConfig
from cronwatch.history import JobHistory
from cronwatch.sla import (
    SLAPolicy,
    SLAViolation,
    check_sla,
    check_all_slas,
    parse_sla_policy,
)


@pytest.fixture()
def history_dir(tmp_path):
    return str(tmp_path / "history")


def _make_job(name: str, sla: dict | None = None) -> JobConfig:
    return JobConfig(
        name=name,
        command="echo hi",
        interval=3600,
        sla=sla,
    )


def _add_records(history_dir: str, job_name: str, outcomes: list[str]) -> None:
    """Write a sequence of 'success'/'failure' records into history."""
    hist = JobHistory(job_name, history_dir)
    for outcome in outcomes:
        if outcome == "success":
            hist.add(success=True, duration=1.0)
        else:
            hist.add(success=False, duration=1.0)


def test_parse_sla_policy_defaults():
    policy = parse_sla_policy({})
    assert policy.min_success_rate is None
    assert policy.max_consecutive_failures is None
    assert policy.window == 20


def test_parse_sla_policy_full():
    policy = parse_sla_policy(
        {"min_success_rate": 0.9, "max_consecutive_failures": 3, "window": 10}
    )
    assert policy.min_success_rate == 0.9
    assert policy.max_consecutive_failures == 3
    assert policy.window == 10


def test_no_sla_returns_empty(history_dir):
    job = _make_job("noop")
    assert check_sla(job, history_dir) == []


def test_success_rate_violation(history_dir):
    _add_records(history_dir, "j1", ["success", "failure", "failure", "failure"])
    job = _make_job("j1", sla={"min_success_rate": 0.8, "window": 4})
    violations = check_sla(job, history_dir)
    assert len(violations) == 1
    assert violations[0].reason == "success_rate_below_threshold"
    assert violations[0].current_value == pytest.approx(0.25)


def test_success_rate_satisfied(history_dir):
    _add_records(history_dir, "j2", ["success", "success", "success", "failure"])
    job = _make_job("j2", sla={"min_success_rate": 0.7, "window": 4})
    assert check_sla(job, history_dir) == []


def test_consecutive_failures_violation(history_dir):
    _add_records(history_dir, "j3", ["success", "failure", "failure", "failure"])
    job = _make_job("j3", sla={"max_consecutive_failures": 2})
    violations = check_sla(job, history_dir)
    reasons = [v.reason for v in violations]
    assert "consecutive_failures_exceeded" in reasons


def test_consecutive_failures_satisfied(history_dir):
    _add_records(history_dir, "j4", ["success", "failure", "failure"])
    job = _make_job("j4", sla={"max_consecutive_failures": 3})
    assert check_sla(job, history_dir) == []


def test_check_all_slas_aggregates(history_dir):
    _add_records(history_dir, "a", ["failure"] * 5)
    _add_records(history_dir, "b", ["success"] * 5)
    jobs = [
        _make_job("a", sla={"min_success_rate": 0.5, "window": 5}),
        _make_job("b", sla={"min_success_rate": 0.5, "window": 5}),
    ]
    violations = check_all_slas(jobs, history_dir)
    assert len(violations) == 1
    assert violations[0].job_name == "a"


def test_no_history_no_violation(history_dir):
    """A job with no executions yet should not trigger a rate violation."""
    job = _make_job("newjob", sla={"min_success_rate": 0.9, "window": 10})
    assert check_sla(job, history_dir) == []
