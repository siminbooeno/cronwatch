"""SLA (Service Level Agreement) tracking for cron jobs.

Allows defining expected success-rate and max-consecutive-failure thresholds
per job, and checking whether those thresholds are currently being violated.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import List, Optional

from cronwatch.config import JobConfig
from cronwatch.history import JobHistory


@dataclass
class SLAPolicy:
    """Per-job SLA policy."""
    min_success_rate: Optional[float] = None   # 0.0 – 1.0
    max_consecutive_failures: Optional[int] = None
    window: int = 20  # number of recent executions to consider


@dataclass
class SLAViolation:
    job_name: str
    reason: str
    current_value: float
    threshold: float


def parse_sla_policy(raw: dict) -> SLAPolicy:
    """Build an SLAPolicy from a raw config dict (the 'sla' sub-key)."""
    return SLAPolicy(
        min_success_rate=raw.get("min_success_rate"),
        max_consecutive_failures=raw.get("max_consecutive_failures"),
        window=int(raw.get("window", 20)),
    )


def check_sla(job: JobConfig, history_dir: str) -> List[SLAViolation]:
    """Return a list of SLA violations for *job* (empty when healthy)."""
    raw_sla = getattr(job, "sla", None)
    if not raw_sla:
        return []

    policy = parse_sla_policy(raw_sla) if isinstance(raw_sla, dict) else raw_sla
    hist = JobHistory(job.name, history_dir)
    violations: List[SLAViolation] = []

    if policy.min_success_rate is not None:
        rate = hist.success_rate(window=policy.window)
        if rate is not None and rate < policy.min_success_rate:
            violations.append(SLAViolation(
                job_name=job.name,
                reason="success_rate_below_threshold",
                current_value=rate,
                threshold=policy.min_success_rate,
            ))

    if policy.max_consecutive_failures is not None:
        consec = hist.consecutive_failures()
        if consec > policy.max_consecutive_failures:
            violations.append(SLAViolation(
                job_name=job.name,
                reason="consecutive_failures_exceeded",
                current_value=float(consec),
                threshold=float(policy.max_consecutive_failures),
            ))

    return violations


def check_all_slas(jobs: List[JobConfig], history_dir: str) -> List[SLAViolation]:
    """Aggregate SLA violations across all jobs."""
    results: List[SLAViolation] = []
    for job in jobs:
        results.extend(check_sla(job, history_dir))
    return results
