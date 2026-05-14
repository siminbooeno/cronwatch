"""Tests for cronwatch.metrics."""
import pytest
from cronwatch.metrics import (
    increment,
    get_counter,
    reset_counter,
    all_counters,
    record_job_run,
)


@pytest.fixture()
def state_dir(tmp_path):
    return str(tmp_path)


def test_get_counter_missing_returns_zero(state_dir):
    assert get_counter(state_dir, "nonexistent") == 0


def test_increment_creates_counter(state_dir):
    increment(state_dir, "alerts.sent")
    assert get_counter(state_dir, "alerts.sent") == 1


def test_increment_accumulates(state_dir):
    for _ in range(5):
        increment(state_dir, "total.runs")
    assert get_counter(state_dir, "total.runs") == 5


def test_increment_by_amount(state_dir):
    increment(state_dir, "batch", amount=10)
    assert get_counter(state_dir, "batch") == 10


def test_reset_counter_sets_to_zero(state_dir):
    increment(state_dir, "x", 7)
    reset_counter(state_dir, "x")
    assert get_counter(state_dir, "x") == 0


def test_reset_counter_nonexistent_is_noop(state_dir):
    reset_counter(state_dir, "ghost")
    assert get_counter(state_dir, "ghost") == 0


def test_all_counters_empty(state_dir):
    assert all_counters(state_dir) == {}


def test_all_counters_returns_snapshot(state_dir):
    increment(state_dir, "a")
    increment(state_dir, "b", 3)
    result = all_counters(state_dir)
    assert result["a"] == 1
    assert result["b"] == 3


def test_record_job_run_success(state_dir):
    record_job_run(state_dir, "backup", success=True)
    assert get_counter(state_dir, "job.backup.runs") == 1
    assert get_counter(state_dir, "job.backup.successes") == 1
    assert get_counter(state_dir, "job.backup.failures") == 0
    assert get_counter(state_dir, "total.runs") == 1
    assert get_counter(state_dir, "total.failures") == 0


def test_record_job_run_failure(state_dir):
    record_job_run(state_dir, "backup", success=False)
    assert get_counter(state_dir, "job.backup.failures") == 1
    assert get_counter(state_dir, "total.failures") == 1


def test_multiple_jobs_independent(state_dir):
    record_job_run(state_dir, "alpha", success=True)
    record_job_run(state_dir, "beta", success=False)
    assert get_counter(state_dir, "job.alpha.runs") == 1
    assert get_counter(state_dir, "job.beta.runs") == 1
    assert get_counter(state_dir, "total.runs") == 2
