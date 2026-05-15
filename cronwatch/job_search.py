"""Full-text and field search across job configurations."""
from __future__ import annotations

from dataclasses import dataclass
from typing import List, Optional

from cronwatch.config import CronwatchConfig, JobConfig


@dataclass
class SearchResult:
    job: JobConfig
    matched_fields: List[str]

    def as_dict(self) -> dict:
        return {
            "name": self.job.name,
            "command": self.job.command,
            "matched_fields": self.matched_fields,
        }


def _field_contains(value: object, query: str) -> bool:
    if value is None:
        return False
    return query.lower() in str(value).lower()


def search_jobs(
    config: CronwatchConfig,
    query: str,
    fields: Optional[List[str]] = None,
) -> List[SearchResult]:
    """Search jobs by a query string across specified fields.

    If *fields* is None, all searchable fields are checked.
    """
    default_fields = ["name", "command", "tags", "labels"]
    target_fields = fields if fields is not None else default_fields

    results: List[SearchResult] = []
    for job in config.jobs:
        matched: List[str] = []
        for field in target_fields:
            value = getattr(job, field, None)
            if isinstance(value, list):
                if any(_field_contains(item, query) for item in value):
                    matched.append(field)
            elif isinstance(value, dict):
                if any(
                    _field_contains(k, query) or _field_contains(v, query)
                    for k, v in value.items()
                ):
                    matched.append(field)
            elif _field_contains(value, query):
                matched.append(field)
        if matched:
            results.append(SearchResult(job=job, matched_fields=matched))
    return results


def find_job_by_name(config: CronwatchConfig, name: str) -> Optional[JobConfig]:
    """Return the first job whose name matches exactly (case-insensitive)."""
    name_lower = name.lower()
    for job in config.jobs:
        if job.name.lower() == name_lower:
            return job
    return None
