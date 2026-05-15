"""Job priority levels and priority-aware alert filtering."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Optional

from cronwatch.config import CronwatchConfig, JobConfig

PRIORITY_LEVELS = {"critical": 0, "high": 1, "medium": 2, "low": 3}
DEFAULT_PRIORITY = "medium"


@dataclass
class PriorityPolicy:
    level: str = DEFAULT_PRIORITY
    alert_on_miss: bool = True
    alert_on_failure: bool = True
    # minimum consecutive failures before alerting (low-priority jobs)
    min_failures_before_alert: int = 1


def _parse_priority(raw: dict) -> PriorityPolicy:
    level = raw.get("level", DEFAULT_PRIORITY).lower()
    if level not in PRIORITY_LEVELS:
        raise ValueError(f"Unknown priority level '{level}'. Valid: {list(PRIORITY_LEVELS)}")
    return PriorityPolicy(
        level=level,
        alert_on_miss=bool(raw.get("alert_on_miss", True)),
        alert_on_failure=bool(raw.get("alert_on_failure", True)),
        min_failures_before_alert=int(raw.get("min_failures_before_alert", 1)),
    )


def parse_priority_policies(cfg: CronwatchConfig) -> Dict[str, PriorityPolicy]:
    """Return a mapping of job_name -> PriorityPolicy for all jobs."""
    policies: Dict[str, PriorityPolicy] = {}
    for job in cfg.jobs:
        raw = job.raw.get("priority", {}) if hasattr(job, "raw") else {}
        if isinstance(raw, str):
            raw = {"level": raw}
        policies[job.name] = _parse_priority(raw)
    return policies


def priority_value(policy: PriorityPolicy) -> int:
    return PRIORITY_LEVELS.get(policy.level, PRIORITY_LEVELS[DEFAULT_PRIORITY])


def should_alert(
    policy: PriorityPolicy,
    event: str,
    consecutive_failures: int = 1,
) -> bool:
    """Decide whether an alert should fire given the policy and event type.

    Args:
        policy: The PriorityPolicy for the job.
        event: One of 'miss', 'failure'.
        consecutive_failures: Number of consecutive failures so far.
    """
    if event == "miss" and not policy.alert_on_miss:
        return False
    if event == "failure":
        if not policy.alert_on_failure:
            return False
        if consecutive_failures < policy.min_failures_before_alert:
            return False
    return True


def jobs_by_priority(jobs: List[JobConfig], policies: Dict[str, PriorityPolicy]) -> List[JobConfig]:
    """Return jobs sorted from highest to lowest priority."""
    return sorted(
        jobs,
        key=lambda j: priority_value(policies.get(j.name, PriorityPolicy())),
    )
