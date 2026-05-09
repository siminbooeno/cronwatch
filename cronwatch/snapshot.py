"""Point-in-time snapshot of all job statuses for reporting and diffing."""

from __future__ import annotations

import json
import os
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from typing import Dict, List, Optional

from cronwatch.config import CronwatchConfig
from cronwatch.history import JobHistory
from cronwatch.state import last_seen_dt


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


@dataclass
class JobSnapshot:
    job_name: str
    last_seen: Optional[str]  # ISO-8601 or None
    success_rate: float        # 0.0 – 1.0
    consecutive_failures: int
    tags: List[str]


@dataclass
class Snapshot:
    captured_at: str           # ISO-8601
    jobs: List[JobSnapshot]

    def as_dict(self) -> dict:
        return asdict(self)


def capture_snapshot(
    cfg: CronwatchConfig,
    state_dir: str,
    history_dir: str,
) -> Snapshot:
    """Build a Snapshot from current state and history."""
    jobs: List[JobSnapshot] = []
    for job in cfg.jobs:
        dt = last_seen_dt(job.name, state_dir)
        hist = JobHistory(job.name, history_dir)
        jobs.append(
            JobSnapshot(
                job_name=job.name,
                last_seen=dt.isoformat() if dt else None,
                success_rate=hist.success_rate(),
                consecutive_failures=hist.consecutive_failures(),
                tags=list(job.tags),
            )
        )
    return Snapshot(captured_at=_utcnow().isoformat(), jobs=jobs)


def save_snapshot(snapshot: Snapshot, path: str) -> None:
    """Persist a snapshot to a JSON file."""
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w") as fh:
        json.dump(snapshot.as_dict(), fh, indent=2)


def load_snapshot(path: str) -> Optional[Snapshot]:
    """Load a previously saved snapshot, or return None if missing."""
    if not os.path.exists(path):
        return None
    with open(path) as fh:
        data = json.load(fh)
    jobs = [
        JobSnapshot(**j) for j in data.get("jobs", [])
    ]
    return Snapshot(captured_at=data["captured_at"], jobs=jobs)


def diff_snapshots(
    previous: Snapshot, current: Snapshot
) -> Dict[str, dict]:
    """Return a mapping of job_name -> changed fields between two snapshots."""
    prev_map = {j.job_name: j for j in previous.jobs}
    curr_map = {j.job_name: j for j in current.jobs}
    changes: Dict[str, dict] = {}
    for name, curr in curr_map.items():
        prev = prev_map.get(name)
        if prev is None:
            changes[name] = {"new": True}
            continue
        delta: dict = {}
        if prev.last_seen != curr.last_seen:
            delta["last_seen"] = {"from": prev.last_seen, "to": curr.last_seen}
        if abs(prev.success_rate - curr.success_rate) > 0.001:
            delta["success_rate"] = {"from": prev.success_rate, "to": curr.success_rate}
        if prev.consecutive_failures != curr.consecutive_failures:
            delta["consecutive_failures"] = {
                "from": prev.consecutive_failures,
                "to": curr.consecutive_failures,
            }
        if delta:
            changes[name] = delta
    return changes
