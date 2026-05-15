"""Per-job alert thresholds: define when a job is considered degraded vs critical."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import List, Optional

from cronwatch.config import CronwatchConfig, JobConfig
from cronwatch.history import JobHistory


@dataclass
class ThresholdPolicy:
    """Alert thresholds for a single job."""
    warn_failure_rate: float = 0.2   # warn if failure rate exceeds this
    crit_failure_rate: float = 0.5   # critical if failure rate exceeds this
    warn_consecutive: int = 2        # warn after N consecutive failures
    crit_consecutive: int = 5        # critical after N consecutive failures


@dataclass
class ThresholdViolation:
    job_name: str
    level: str          # "warn" or "crit"
    reason: str
    failure_rate: float
    consecutive_failures: int


def _parse_threshold(raw: dict) -> ThresholdPolicy:
    t = raw.get("thresholds", {})
    return ThresholdPolicy(
        warn_failure_rate=float(t.get("warn_failure_rate", 0.2)),
        crit_failure_rate=float(t.get("crit_failure_rate", 0.5)),
        warn_consecutive=int(t.get("warn_consecutive", 2)),
        crit_consecutive=int(t.get("crit_consecutive", 5)),
    )


def parse_threshold_policies(cfg: CronwatchConfig) -> dict[str, ThresholdPolicy]:
    """Return a mapping of job name -> ThresholdPolicy."""
    result: dict[str, ThresholdPolicy] = {}
    for job in cfg.jobs:
        raw = job.__dict__ if hasattr(job, "__dict__") else {}
        result[job.name] = _parse_threshold(raw)
    return result


def check_thresholds(
    job: JobConfig,
    history_dir: str,
    policy: Optional[ThresholdPolicy] = None,
    window: int = 20,
) -> Optional[ThresholdViolation]:
    """Check a single job's history against its threshold policy."""
    if policy is None:
        policy = ThresholdPolicy()
    hist = JobHistory(history_dir, job.name)
    rate = hist.success_rate(window)
    consec = hist.consecutive_failures()
    failure_rate = 1.0 - rate

    level: Optional[str] = None
    reason = ""

    if failure_rate >= policy.crit_failure_rate or consec >= policy.crit_consecutive:
        level = "crit"
        reason = (
            f"failure_rate={failure_rate:.0%} (threshold={policy.crit_failure_rate:.0%}), "
            f"consecutive={consec} (threshold={policy.crit_consecutive})"
        )
    elif failure_rate >= policy.warn_failure_rate or consec >= policy.warn_consecutive:
        level = "warn"
        reason = (
            f"failure_rate={failure_rate:.0%} (threshold={policy.warn_failure_rate:.0%}), "
            f"consecutive={consec} (threshold={policy.warn_consecutive})"
        )

    if level is None:
        return None
    return ThresholdViolation(
        job_name=job.name,
        level=level,
        reason=reason,
        failure_rate=failure_rate,
        consecutive_failures=consec,
    )


def check_all_thresholds(
    cfg: CronwatchConfig,
    history_dir: str,
    window: int = 20,
) -> List[ThresholdViolation]:
    """Check thresholds for all jobs; return list of violations."""
    policies = parse_threshold_policies(cfg)
    violations: List[ThresholdViolation] = []
    for job in cfg.jobs:
        policy = policies.get(job.name, ThresholdPolicy())
        v = check_thresholds(job, history_dir, policy, window)
        if v is not None:
            violations.append(v)
    return violations
