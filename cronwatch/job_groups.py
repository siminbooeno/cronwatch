"""Job grouping: define named groups of jobs and query membership."""
from __future__ import annotations

import json
import os
from typing import Dict, List, Optional

from cronwatch.config import CronwatchConfig, JobConfig


# ---------------------------------------------------------------------------
# Types
# ---------------------------------------------------------------------------

class JobGroup:
    """A named collection of job names."""

    def __init__(self, name: str, job_names: List[str], description: str = "") -> None:
        self.name = name
        self.job_names = list(job_names)
        self.description = description

    def __repr__(self) -> str:  # pragma: no cover
        return f"JobGroup(name={self.name!r}, jobs={self.job_names!r})"


# ---------------------------------------------------------------------------
# Parsing
# ---------------------------------------------------------------------------

def _parse_group(raw: dict) -> JobGroup:
    name = raw["name"]
    job_names = list(raw.get("jobs", []))
    description = raw.get("description", "")
    return JobGroup(name=name, job_names=job_names, description=description)


def load_groups(path: str) -> List[JobGroup]:
    """Load job groups from a JSON file.  Returns empty list if file is absent."""
    if not os.path.exists(path):
        return []
    with open(path, "r", encoding="utf-8") as fh:
        data = json.load(fh)
    return [_parse_group(r) for r in data.get("groups", [])]


# ---------------------------------------------------------------------------
# Query helpers
# ---------------------------------------------------------------------------

def jobs_in_group(group: JobGroup, cfg: CronwatchConfig) -> List[JobConfig]:
    """Return JobConfig objects whose names are listed in *group*."""
    by_name: Dict[str, JobConfig] = {j.name: j for j in cfg.jobs}
    return [by_name[n] for n in group.job_names if n in by_name]


def find_group(groups: List[JobGroup], name: str) -> Optional[JobGroup]:
    """Return the first group matching *name*, or None."""
    for g in groups:
        if g.name == name:
            return g
    return None


def groups_for_job(groups: List[JobGroup], job_name: str) -> List[JobGroup]:
    """Return all groups that contain *job_name*."""
    return [g for g in groups if job_name in g.job_names]


def all_group_names(groups: List[JobGroup]) -> List[str]:
    """Return a sorted list of unique group names."""
    return sorted({g.name for g in groups})
