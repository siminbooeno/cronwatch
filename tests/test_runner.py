"""Tests for cronwatch.runner (including history integration)."""

import pytest

from cronwatch.config import JobConfig
from cronwatch.history import load_history
from cronwatch.runner import run_job
from cronwatch.state import load_store


@pytest.fixture
def tmp_state(tmp_path):
    return str(tmp_path / "state")


def make_job(name="test_job", command="true", timeout=None):
    return JobConfig(name=name, command=command, interval=60, timeout=timeout)


def test_run_job_success_returns_true(tmp_state):
    job = make_job(command="true")
    assert run_job(job, tmp_state) is True


def test_run_job_failure_returns_false(tmp_state):
    job = make_job(command="false")
    assert run_job(job, tmp_state) is False


def test_run_job_records_success_in_state(tmp_state):
    job = make_job(command="true")
    run_job(job, tmp_state)
    store = load_store(tmp_state)
    assert store[job.name]["failure_count"] == 0


def test_run_job_records_failure_in_state(tmp_state):
    job = make_job(command="false")
    run_job(job, tmp_state)
    store = load_store(tmp_state)
    assert store[job.name]["failure_count"] == 1


def test_run_job_appends_history_on_success(tmp_state):
    job = make_job(name="hist_job", command="true")
    run_job(job, tmp_state)
    h = load_history(tmp_state, "hist_job")
    assert len(h.records) == 1
    assert h.records[0].success is True
    assert h.records[0].exit_code == 0
    assert h.records[0].duration_seconds is not None


def test_run_job_appends_history_on_failure(tmp_state):
    job = make_job(name="fail_job", command="false")
    run_job(job, tmp_state)
    h = load_history(tmp_state, "fail_job")
    assert len(h.records) == 1
    assert h.records[0].success is False
    assert h.records[0].exit_code == 1


def test_run_job_timeout_records_failure(tmp_state):
    job = make_job(name="slow_job", command="sleep 10", timeout=1)
    result = run_job(job, tmp_state)
    assert result is False
    h = load_history(tmp_state, "slow_job")
    assert h.records[0].note is not None
    assert "timed out" in h.records[0].note


def test_run_job_multiple_runs_accumulate_history(tmp_state):
    job = make_job(name="multi", command="true")
    run_job(job, tmp_state)
    run_job(job, tmp_state)
    run_job(job, tmp_state)
    h = load_history(tmp_state, "multi")
    assert len(h.records) == 3
    assert h.success_rate() == 1.0
