"""Aggregate per-job status derived from history and state."""
from __future__ import annotations

import os
from dataclasses import dataclass
from typing import Optional

from cronwatch.config import JobConfig, CronwatchConfig
from cronwatch.history import JobHistory
from cronwatch.state import last_seen_dt


@dataclass
class JobStatus:
    job_name: str
    status: str          # "healthy" | "failing" | "unknown"
    last_success: Optional[str]
    last_failure: Optional[str]
    consecutive_failures: int
    success_rate: float  # 0.0 – 1.0, or -1.0 when no history
    total_runs: int


def _status_from_history(history: JobHistory) -> str:
    if history.total == 0:
        return "unknown"
    if history.consecutive_failures() > 0:
        return "failing"
    return "healthy"


def get_job_status(job: JobConfig, history_dir: str) -> JobStatus:
    """Return a JobStatus for *job* using data stored in *history_dir*."""
    history = JobHistory(job.name, history_dir)
    status = _status_from_history(history)
    last_ok = history.last_success()
    last_fail = history.last_failure() if hasattr(history, "last_failure") else None
    rate = history.success_rate() if history.total > 0 else -1.0
    return JobStatus(
        job_name=job.name,
        status=status,
        last_success=last_ok,
        last_failure=last_fail,
        consecutive_failures=history.consecutive_failures(),
        success_rate=rate,
        total_runs=history.total,
    )


def get_all_statuses(config: CronwatchConfig, history_dir: str) -> list[JobStatus]:
    """Return a JobStatus for every job defined in *config*."""
    return [get_job_status(job, history_dir) for job in config.jobs]


def format_status_table(statuses: list[JobStatus]) -> str:
    """Render a plain-text table of job statuses."""
    if not statuses:
        return "No jobs configured."
    header = f"{'JOB':<30} {'STATUS':<10} {'RUNS':>6} {'RATE':>7} {'CONSEC_FAIL':>12}  LAST_SUCCESS"
    sep = "-" * len(header)
    rows = [header, sep]
    for s in statuses:
        rate_str = f"{s.success_rate * 100:.1f}%" if s.success_rate >= 0 else "  n/a"
        last_ok = s.last_success or "never"
        rows.append(
            f"{s.job_name:<30} {s.status:<10} {s.total_runs:>6} {rate_str:>7}"
            f" {s.consecutive_failures:>12}  {last_ok}"
        )
    return "\n".join(rows)
