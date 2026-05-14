"""Per-job retention policy: define how long history and state are kept per job."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Optional

from cronwatch.config import CronwatchConfig, JobConfig


@dataclass
class RetentionPolicy:
    """Retention settings for a single job or global default."""
    history_days: int = 30
    max_records: Optional[int] = None  # cap on number of history records kept
    state_days: int = 90


_DEFAULT_POLICY = RetentionPolicy()


def _parse_policy(raw: dict) -> RetentionPolicy:
    """Parse a retention policy dict from config."""
    return RetentionPolicy(
        history_days=int(raw.get("history_days", _DEFAULT_POLICY.history_days)),
        max_records=int(raw["max_records"]) if "max_records" in raw else None,
        state_days=int(raw.get("state_days", _DEFAULT_POLICY.state_days)),
    )


def parse_retention_policies(
    config: CronwatchConfig,
) -> Dict[str, RetentionPolicy]:
    """Return a mapping of job_name -> RetentionPolicy.

    Jobs without an explicit policy inherit the global default (or the
    project-level default if no global section is present).
    """
    global_raw = getattr(config, "retention", None) or {}
    global_policy = _parse_policy(global_raw) if global_raw else _DEFAULT_POLICY

    policies: Dict[str, RetentionPolicy] = {}
    for job in config.jobs:
        job_raw = getattr(job, "retention", None) or {}
        if job_raw:
            # Merge: job overrides global
            merged = {
                "history_days": global_policy.history_days,
                "state_days": global_policy.state_days,
            }
            merged.update(job_raw)
            policies[job.name] = _parse_policy(merged)
        else:
            policies[job.name] = global_policy
    return policies


def effective_policy(
    job_name: str,
    policies: Dict[str, RetentionPolicy],
) -> RetentionPolicy:
    """Return the effective RetentionPolicy for a job, falling back to default."""
    return policies.get(job_name, _DEFAULT_POLICY)
