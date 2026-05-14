"""Job pause/resume support — temporarily suppress scheduling and alerts for a job."""

from __future__ import annotations

import json
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


def _pauses_path(state_dir: str, job_name: str) -> Path:
    return Path(state_dir) / "pauses" / f"{job_name}.json"


def pause_job(
    state_dir: str,
    job_name: str,
    reason: str = "",
    until: Optional[datetime] = None,
) -> dict:
    """Pause a job.  Returns the pause record written to disk."""
    path = _pauses_path(state_dir, job_name)
    path.parent.mkdir(parents=True, exist_ok=True)

    record = {
        "job": job_name,
        "paused_at": _utcnow().isoformat(),
        "reason": reason,
        "until": until.isoformat() if until else None,
    }
    path.write_text(json.dumps(record))
    return record


def resume_job(state_dir: str, job_name: str) -> bool:
    """Remove the pause record.  Returns True if a record existed."""
    path = _pauses_path(state_dir, job_name)
    if path.exists():
        path.unlink()
        return True
    return False


def is_paused(state_dir: str, job_name: str) -> bool:
    """Return True if the job is currently paused (and the pause has not expired)."""
    path = _pauses_path(state_dir, job_name)
    if not path.exists():
        return False
    try:
        record = json.loads(path.read_text())
    except (json.JSONDecodeError, OSError):
        return False

    until_raw = record.get("until")
    if until_raw is None:
        return True  # paused indefinitely

    until_dt = datetime.fromisoformat(until_raw)
    if _utcnow() < until_dt:
        return True

    # Pause has expired — clean up automatically
    path.unlink(missing_ok=True)
    return False


def get_pause_record(state_dir: str, job_name: str) -> Optional[dict]:
    """Return the raw pause record, or None if the job is not paused."""
    if not is_paused(state_dir, job_name):
        return None
    path = _pauses_path(state_dir, job_name)
    try:
        return json.loads(path.read_text())
    except (json.JSONDecodeError, OSError):
        return None


def list_paused_jobs(state_dir: str) -> list[dict]:
    """Return pause records for every currently-paused job."""
    pauses_dir = Path(state_dir) / "pauses"
    if not pauses_dir.exists():
        return []
    results = []
    for p in sorted(pauses_dir.glob("*.json")):
        job_name = p.stem
        record = get_pause_record(state_dir, job_name)
        if record is not None:
            results.append(record)
    return results
