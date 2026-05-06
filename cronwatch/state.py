"""Job state persistence for tracking last execution times and statuses."""

import json
import os
from dataclasses import dataclass, field, asdict
from datetime import datetime
from typing import Optional, Dict


@dataclass
class JobState:
    job_id: str
    last_seen: Optional[str] = None  # ISO format datetime string
    last_status: Optional[str] = None  # 'success' | 'failed' | 'missed'
    failure_count: int = 0
    miss_count: int = 0

    def last_seen_dt(self) -> Optional[datetime]:
        if self.last_seen is None:
            return None
        return datetime.fromisoformat(self.last_seen)

    def record_success(self) -> None:
        self.last_seen = datetime.utcnow().isoformat()
        self.last_status = "success"
        self.failure_count = 0

    def record_failure(self) -> None:
        self.last_seen = datetime.utcnow().isoformat()
        self.last_status = "failed"
        self.failure_count += 1

    def record_miss(self) -> None:
        self.last_status = "missed"
        self.miss_count += 1


class StateStore:
    def __init__(self, state_file: str = ".cronwatch_state.json"):
        self.state_file = state_file
        self._states: Dict[str, JobState] = {}
        self._load()

    def _load(self) -> None:
        if not os.path.exists(self.state_file):
            return
        with open(self.state_file, "r") as f:
            raw = json.load(f)
        for job_id, data in raw.items():
            self._states[job_id] = JobState(**data)

    def save(self) -> None:
        with open(self.state_file, "w") as f:
            json.dump(
                {k: asdict(v) for k, v in self._states.items()},
                f,
                indent=2,
            )

    def get(self, job_id: str) -> JobState:
        if job_id not in self._states:
            self._states[job_id] = JobState(job_id=job_id)
        return self._states[job_id]

    def all_states(self) -> Dict[str, JobState]:
        return dict(self._states)
