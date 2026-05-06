"""Checks whether cron jobs have run on schedule and updates state accordingly."""

from datetime import datetime, timedelta
from typing import List, Tuple

from cronwatch.config import JobConfig
from cronwatch.state import JobState, StateStore


def is_job_overdue(job: JobConfig, state: JobState, now: datetime) -> bool:
    """Return True if the job has not been seen within its expected interval."""
    last_seen = state.last_seen_dt()
    if last_seen is None:
        # Never recorded — treat as overdue only if monitor has been running
        # longer than the interval (we use a grace period equal to interval).
        return False
    threshold = last_seen + timedelta(seconds=job.interval_seconds)
    grace = timedelta(seconds=job.grace_period_seconds)
    return now > threshold + grace


def check_jobs(
    jobs: List[JobConfig],
    store: StateStore,
    now: datetime | None = None,
) -> List[Tuple[JobConfig, JobState]]:
    """Check all jobs and return list of (job, state) pairs that are overdue."""
    if now is None:
        now = datetime.utcnow()

    overdue: List[Tuple[JobConfig, JobState]] = []
    for job in jobs:
        state = store.get(job.id)
        if is_job_overdue(job, state, now):
            state.record_miss()
            overdue.append((job, state))
    store.save()
    return overdue


def record_heartbeat(job_id: str, store: StateStore, success: bool = True) -> JobState:
    """Record a heartbeat ping for a job (called when job reports in)."""
    state = store.get(job_id)
    if success:
        state.record_success()
    else:
        state.record_failure()
    store.save()
    return state
