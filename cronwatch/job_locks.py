"""Job execution locking — prevent concurrent runs of the same job."""

from __future__ import annotations

import json
import os
import time
from pathlib import Path
from typing import Optional


def _utcnow() -> float:
    return time.time()


def _lock_path(state_dir: str, job_name: str) -> Path:
    return Path(state_dir) / "locks" / f"{job_name}.lock"


def _load_lock(path: Path) -> Optional[dict]:
    try:
        with path.open() as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return None


def _save_lock(path: Path, data: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w") as f:
        json.dump(data, f)


def acquire_lock(state_dir: str, job_name: str, ttl_seconds: int = 3600) -> bool:
    """Attempt to acquire a lock for job_name.

    Returns True if the lock was acquired, False if already locked.
    A lock older than ttl_seconds is considered stale and will be overwritten.
    """
    path = _lock_path(state_dir, job_name)
    existing = _load_lock(path)
    now = _utcnow()

    if existing is not None:
        acquired_at = existing.get("acquired_at", 0)
        if now - acquired_at < ttl_seconds:
            return False  # valid lock held by another process

    _save_lock(path, {
        "job": job_name,
        "acquired_at": now,
        "pid": os.getpid(),
        "ttl_seconds": ttl_seconds,
    })
    return True


def release_lock(state_dir: str, job_name: str) -> bool:
    """Release the lock for job_name. Returns True if it existed."""
    path = _lock_path(state_dir, job_name)
    if path.exists():
        path.unlink()
        return True
    return False


def is_locked(state_dir: str, job_name: str, ttl_seconds: int = 3600) -> bool:
    """Return True if job_name currently holds a non-stale lock."""
    path = _lock_path(state_dir, job_name)
    existing = _load_lock(path)
    if existing is None:
        return False
    age = _utcnow() - existing.get("acquired_at", 0)
    return age < ttl_seconds


def lock_info(state_dir: str, job_name: str) -> Optional[dict]:
    """Return raw lock data for job_name, or None if not locked."""
    return _load_lock(_lock_path(state_dir, job_name))
