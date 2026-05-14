"""Job dependency tracking: ensure a job only runs after its dependencies succeed."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import List, Optional

from cronwatch.config import CronwatchConfig, JobConfig
from cronwatch.history import JobHistory


@dataclass
class DependencyResult:
    job_name: str
    satisfied: bool
    blocking_deps: List[str] = field(default_factory=list)
    reason: Optional[str] = None


def _last_success_within(job_name: str, history_dir: str, within_seconds: float) -> bool:
    """Return True if job_name had a successful run within the last `within_seconds`."""
    import time
    history = JobHistory(history_dir, job_name)
    last = history.last_success()
    if last is None:
        return False
    age = time.time() - last.timestamp()
    return age <= within_seconds


def check_dependencies(
    job: JobConfig,
    config: CronwatchConfig,
    history_dir: str,
) -> DependencyResult:
    """Check whether all declared dependencies for *job* are satisfied."""
    deps: List[str] = getattr(job, "depends_on", None) or []
    if not deps:
        return DependencyResult(job_name=job.name, satisfied=True)

    job_map = {j.name: j for j in config.jobs}
    blocking: List[str] = []

    for dep_name in deps:
        dep_job = job_map.get(dep_name)
        if dep_job is None:
            blocking.append(dep_name)
            continue
        # A dependency is satisfied if it succeeded within its own interval + grace
        window = (dep_job.interval_seconds or 3600) + (dep_job.grace_seconds or 0)
        if not _last_success_within(dep_name, history_dir, window):
            blocking.append(dep_name)

    if blocking:
        return DependencyResult(
            job_name=job.name,
            satisfied=False,
            blocking_deps=blocking,
            reason=f"Waiting for: {', '.join(blocking)}",
        )
    return DependencyResult(job_name=job.name, satisfied=True)


def filter_ready_jobs(
    jobs: List[JobConfig],
    config: CronwatchConfig,
    history_dir: str,
) -> List[JobConfig]:
    """Return only those jobs whose dependencies are all satisfied."""
    return [
        j for j in jobs
        if check_dependencies(j, config, history_dir).satisfied
    ]
