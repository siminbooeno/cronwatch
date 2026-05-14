"""Key-value label support for cron jobs — filter, query, and select jobs by labels."""
from __future__ import annotations

from typing import Dict, List

from cronwatch.config import CronwatchConfig, JobConfig


def jobs_with_label(config: CronwatchConfig, key: str, value: str) -> List[JobConfig]:
    """Return jobs whose labels contain the given key=value pair."""
    return [
        job for job in config.jobs
        if job.labels.get(key) == value
    ]


def jobs_matching_selector(config: CronwatchConfig, selector: Dict[str, str]) -> List[JobConfig]:
    """Return jobs whose labels are a superset of the selector dict."""
    result = []
    for job in config.jobs:
        if all(job.labels.get(k) == v for k, v in selector.items()):
            result.append(job)
    return result


def all_label_keys(config: CronwatchConfig) -> List[str]:
    """Return a sorted list of all distinct label keys across all jobs."""
    keys: set = set()
    for job in config.jobs:
        keys.update(job.labels.keys())
    return sorted(keys)


def all_label_values(config: CronwatchConfig, key: str) -> List[str]:
    """Return a sorted list of all distinct values for a given label key."""
    values: set = set()
    for job in config.jobs:
        if key in job.labels:
            values.add(job.labels[key])
    return sorted(values)


def parse_selector(selector_str: str) -> Dict[str, str]:
    """Parse a comma-separated key=value selector string into a dict.

    Example: "env=prod,team=infra" -> {"env": "prod", "team": "infra"}
    Raises ValueError on malformed input.
    """
    result: Dict[str, str] = {}
    if not selector_str.strip():
        return result
    for part in selector_str.split(","):
        part = part.strip()
        if "=" not in part:
            raise ValueError(f"Invalid selector segment (expected key=value): {part!r}")
        k, v = part.split("=", 1)
        k, v = k.strip(), v.strip()
        if not k:
            raise ValueError(f"Empty key in selector segment: {part!r}")
        result[k] = v
    return result
