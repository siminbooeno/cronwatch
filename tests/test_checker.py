"""Tests for cronwatch.checker module."""

from datetime import datetime, timedelta

import pytest

from cronwatch.config import JobConfig
from cronwatch.state import JobState, StateStore
from cronwatch.checker import is_job_overdue, check_jobs, record_heartbeat


@pytest.fixture
def tmp_store(tmp_path):
    return StateStore(str(tmp_path / "state.json"))


def make_job(job_id="backup", interval=3600, grace=60):
    return JobConfig(id=job_id, name=job_id, interval_seconds=interval, grace_period_seconds=grace)


def test_job_never_seen_is_not_overdue(tmp_store):
    job = make_job()
    state = tmp_store.get(job.id)
    now = datetime.utcnow()
    assert not is_job_overdue(job, state, now)


def test_job_recently_seen_is_not_overdue(tmp_store):
    job = make_job(interval=3600, grace=60)
    state = tmp_store.get(job.id)
    state.record_success()
    now = datetime.utcnow() + timedelta(seconds=3000)
    assert not is_job_overdue(job, state, now)


def test_job_past_interval_plus_grace_is_overdue(tmp_store):
    job = make_job(interval=3600, grace=60)
    state = tmp_store.get(job.id)
    state.record_success()
    now = datetime.utcnow() + timedelta(seconds=3700)
    assert is_job_overdue(job, state, now)


def test_job_within_grace_is_not_overdue(tmp_store):
    job = make_job(interval=3600, grace=120)
    state = tmp_store.get(job.id)
    state.record_success()
    now = datetime.utcnow() + timedelta(seconds=3650)
    assert not is_job_overdue(job, state, now)


def test_check_jobs_returns_overdue(tmp_store):
    job = make_job(interval=3600, grace=60)
    state = tmp_store.get(job.id)
    state.record_success()
    tmp_store.save()
    now = datetime.utcnow() + timedelta(seconds=3700)
    overdue = check_jobs([job], tmp_store, now=now)
    assert len(overdue) == 1
    assert overdue[0][0].id == job.id


def test_check_jobs_records_miss(tmp_store):
    job = make_job(interval=3600, grace=60)
    state = tmp_store.get(job.id)
    state.record_success()
    tmp_store.save()
    now = datetime.utcnow() + timedelta(seconds=3700)
    check_jobs([job], tmp_store, now=now)
    assert tmp_store.get(job.id).miss_count == 1


def test_record_heartbeat_success(tmp_store):
    state = record_heartbeat("myjob", tmp_store, success=True)
    assert state.last_status == "success"


def test_record_heartbeat_failure(tmp_store):
    state = record_heartbeat("myjob", tmp_store, success=False)
    assert state.last_status == "failed"
    assert state.failure_count == 1
