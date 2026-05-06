"""Tests for cronwatch.state module."""

import json
import os
import tempfile
from datetime import datetime, timedelta

import pytest

from cronwatch.state import JobState, StateStore


@pytest.fixture
def tmp_state_file(tmp_path):
    return str(tmp_path / "test_state.json")


def test_job_state_defaults():
    state = JobState(job_id="backup")
    assert state.last_seen is None
    assert state.last_status is None
    assert state.failure_count == 0
    assert state.miss_count == 0


def test_record_success():
    state = JobState(job_id="backup")
    state.record_success()
    assert state.last_status == "success"
    assert state.last_seen is not None
    assert state.failure_count == 0


def test_record_failure_increments_count():
    state = JobState(job_id="backup")
    state.record_failure()
    state.record_failure()
    assert state.failure_count == 2
    assert state.last_status == "failed"


def test_record_miss_increments_count():
    state = JobState(job_id="backup")
    state.record_miss()
    state.record_miss()
    assert state.miss_count == 2
    assert state.last_status == "missed"


def test_last_seen_dt_returns_datetime():
    state = JobState(job_id="backup")
    state.record_success()
    dt = state.last_seen_dt()
    assert isinstance(dt, datetime)


def test_state_store_creates_new_job(tmp_state_file):
    store = StateStore(tmp_state_file)
    state = store.get("myjob")
    assert state.job_id == "myjob"
    assert state.last_seen is None


def test_state_store_persists_and_reloads(tmp_state_file):
    store = StateStore(tmp_state_file)
    store.get("myjob").record_success()
    store.save()

    store2 = StateStore(tmp_state_file)
    state = store2.get("myjob")
    assert state.last_status == "success"
    assert state.last_seen is not None


def test_state_store_all_states(tmp_state_file):
    store = StateStore(tmp_state_file)
    store.get("job1").record_success()
    store.get("job2").record_failure()
    store.save()
    assert set(store.all_states().keys()) == {"job1", "job2"}
