"""Job execution history tracking with summary statistics."""

from __future__ import annotations

import json
import os
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import List, Optional

MAX_HISTORY_ENTRIES = 100


@dataclass
class ExecutionRecord:
    timestamp: str
    success: bool
    exit_code: Optional[int] = None
    duration_seconds: Optional[float] = None
    note: Optional[str] = None


@dataclass
class JobHistory:
    job_name: str
    records: List[ExecutionRecord] = field(default_factory=list)

    def add(self, record: ExecutionRecord) -> None:
        self.records.append(record)
        if len(self.records) > MAX_HISTORY_ENTRIES:
            self.records = self.records[-MAX_HISTORY_ENTRIES:]

    def success_rate(self) -> Optional[float]:
        if not self.records:
            return None
        successes = sum(1 for r in self.records if r.success)
        return successes / len(self.records)

    def last_success(self) -> Optional[ExecutionRecord]:
        for r in reversed(self.records):
            if r.success:
                return r
        return None

    def last_failure(self) -> Optional[ExecutionRecord]:
        for r in reversed(self.records):
            if not r.success:
                return r
        return None

    def consecutive_failures(self) -> int:
        count = 0
        for r in reversed(self.records):
            if not r.success:
                count += 1
            else:
                break
        return count


def _history_path(state_dir: str, job_name: str) -> Path:
    safe_name = job_name.replace("/", "_").replace(" ", "_")
    return Path(state_dir) / f"{safe_name}.history.json"


def load_history(state_dir: str, job_name: str) -> JobHistory:
    path = _history_path(state_dir, job_name)
    if not path.exists():
        return JobHistory(job_name=job_name)
    with open(path) as f:
        data = json.load(f)
    records = [ExecutionRecord(**r) for r in data.get("records", [])]
    return JobHistory(job_name=job_name, records=records)


def save_history(state_dir: str, history: JobHistory) -> None:
    os.makedirs(state_dir, exist_ok=True)
    path = _history_path(state_dir, history.job_name)
    data = {"job_name": history.job_name, "records": [asdict(r) for r in history.records]}
    with open(path, "w") as f:
        json.dump(data, f, indent=2)


def append_execution(
    state_dir: str,
    job_name: str,
    success: bool,
    exit_code: Optional[int] = None,
    duration_seconds: Optional[float] = None,
    note: Optional[str] = None,
) -> JobHistory:
    history = load_history(state_dir, job_name)
    record = ExecutionRecord(
        timestamp=datetime.now(timezone.utc).isoformat(),
        success=success,
        exit_code=exit_code,
        duration_seconds=duration_seconds,
        note=note,
    )
    history.add(record)
    save_history(state_dir, history)
    return history
