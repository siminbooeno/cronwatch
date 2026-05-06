"""Tests for cronwatch.runner."""

import pytest
from unittest.mock import patch, MagicMock
import subprocess

from cronwatch.config import JobConfig
from cronwatch.runner import run_job


@pytest.fixture
def tmp_state(tmp_path):
    return str(tmp_path)


def make_job(name="test_job", command="echo hello", timeout=None):
    return JobConfig(name=name, schedule="* * * * *", command=command, timeout_seconds=timeout)


def test_run_job_success_returns_true(tmp_state):
    job = make_job(command="echo ok")
    result = run_job(job, state_dir=tmp_state)
    assert result is True


def test_run_job_failure_returns_false(tmp_state):
    job = make_job(command="exit 1")
    result = run_job(job, state_dir=tmp_state)
    assert result is False


def test_run_job_records_success_in_state(tmp_state):
    from cronwatch.state import last_seen_dt
    job = make_job(command="echo hi")
    run_job(job, state_dir=tmp_state)
    assert last_seen_dt(job.name, state_dir=tmp_state) is not None


def test_run_job_records_failure_in_state(tmp_state):
    from cronwatch.state import load_state
    job = make_job(command="exit 2")
    run_job(job, state_dir=tmp_state)
    state = load_state(job.name, state_dir=tmp_state)
    assert state.failure_count >= 1


def test_run_job_timeout_returns_false(tmp_state):
    job = make_job(command="sleep 10", timeout=0.05)
    result = run_job(job, state_dir=tmp_state)
    assert result is False


def test_run_job_timeout_records_failure(tmp_state):
    from cronwatch.state import load_state
    job = make_job(command="sleep 10", timeout=0.05)
    run_job(job, state_dir=tmp_state)
    state = load_state(job.name, state_dir=tmp_state)
    assert state.failure_count >= 1


def test_run_job_no_command_returns_false(tmp_state):
    job = JobConfig(name="empty", schedule="* * * * *", command=None)
    result = run_job(job, state_dir=tmp_state)
    assert result is False


def test_run_job_nonzero_exit_logs_stderr(tmp_state, caplog):
    import logging
    job = make_job(command="bash -c 'echo boom >&2; exit 1'")
    with caplog.at_level(logging.ERROR, logger="cronwatch.runner"):
        run_job(job, state_dir=tmp_state)
    assert any("failed" in r.message for r in caplog.records)
