"""Job timeout tracking and violation detection.

Tracks jobs that exceeded their configured timeout and provides
violation records for alerting.
"""

from __future__ import annotations

import json
import os
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import List, Optional

from cronwatch.config import JobConfig
from cronwatch.history import JobHistory


@dataclass
class TimeoutViolation:
    job_name: str
    timeout_seconds: int
    actual_seconds: float
    occurred_at: str  # ISO-8601


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


def check_timeouts(
    jobs: List[JobConfig],
    history_dir: str,
    window_seconds: int = 3600,
) -> List[TimeoutViolation]:
    """Return TimeoutViolation for each job whose recent runs exceeded timeout.

    Only jobs with a configured ``timeout`` are evaluated.  Within the
    look-back *window_seconds* (default 1 h) every execution record whose
    duration exceeds the job's timeout is reported.
    """
    violations: List[TimeoutViolation] = []
    now = _utcnow()

    for job in jobs:
        timeout = job.raw.get("timeout") if hasattr(job, "raw") else None
        if timeout is None:
            continue
        try:
            timeout_sec = int(timeout)
        except (TypeError, ValueError):
            continue

        hist = JobHistory(history_dir, job.name)
        cutoff = now.timestamp() - window_seconds

        for record in hist.records():
            ts = record.get("timestamp")
            duration = record.get("duration_seconds")
            if ts is None or duration is None:
                continue
            try:
                rec_time = datetime.fromisoformat(ts).timestamp()
            except ValueError:
                continue
            if rec_time < cutoff:
                continue
            if float(duration) > timeout_sec:
                violations.append(
                    TimeoutViolation(
                        job_name=job.name,
                        timeout_seconds=timeout_sec,
                        actual_seconds=float(duration),
                        occurred_at=ts,
                    )
                )

    return violations


def format_violation(v: TimeoutViolation) -> str:
    return (
        f"Job '{v.job_name}' exceeded timeout: "
        f"{v.actual_seconds:.1f}s > {v.timeout_seconds}s "
        f"(at {v.occurred_at})"
    )
