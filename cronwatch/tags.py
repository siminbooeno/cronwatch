"""Tag-based filtering for cron jobs.

Allows jobs to be grouped and filtered by arbitrary string tags,
enabling targeted checks, alerts, and reports.
"""
from __future__ import annotations

from typing import Iterable

from cronwatch.config import CronwatchConfig, JobConfig


def jobs_with_tag(config: CronwatchConfig, tag: str) -> list[JobConfig]:
    """Return all jobs that carry *tag*."""
    return [job for job in config.jobs if tag in (job.tags or [])]


def jobs_without_tag(config: CronwatchConfig, tag: str) -> list[JobConfig]:
    """Return all jobs that do NOT carry *tag*."""
    return [job for job in config.jobs if tag not in (job.tags or [])]


def filter_jobs(
    config: CronwatchConfig,
    include: Iterable[str] | None = None,
    exclude: Iterable[str] | None = None,
) -> list[JobConfig]:
    """Filter jobs by tag inclusion / exclusion lists.

    *include* – keep only jobs that have ALL listed tags.
    *exclude* – drop jobs that have ANY listed tag.
    Both filters may be combined.
    """
    include_tags = list(include or [])
    exclude_tags = list(exclude or [])

    result: list[JobConfig] = []
    for job in config.jobs:
        job_tags: set[str] = set(job.tags or [])
        if include_tags and not all(t in job_tags for t in include_tags):
            continue
        if any(t in job_tags for t in exclude_tags):
            continue
        result.append(job)
    return result


def all_tags(config: CronwatchConfig) -> list[str]:
    """Return a sorted, deduplicated list of every tag used in *config*."""
    seen: set[str] = set()
    for job in config.jobs:
        seen.update(job.tags or [])
    return sorted(seen)
