"""Job cooldown: prevent a job from being re-run within a minimum interval."""

from __future__ import annotations

import json
import os
from datetime import datetime, timezone, timedelta
from typing import Optional


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


def _cooldown_path(state_dir: str, job_name: str) -> str:
    safe = job_name.replace(os.sep, "_")
    return os.path.join(state_dir, f"{safe}.cooldown.json")


def _load_cooldown(path: str) -> dict:
    if not os.path.exists(path):
        return {}
    with open(path) as f:
        return json.load(f)


def _save_cooldown(path: str, data: dict) -> None:
    os.makedirs(os.path.dirname(path) or ".", exist_ok=True)
    with open(path, "w") as f:
        json.dump(data, f)


def set_cooldown(state_dir: str, job_name: str, cooldown_seconds: int) -> dict:
    """Record that a job was just executed; store cooldown expiry."""
    path = _cooldown_path(state_dir, job_name)
    now = _utcnow()
    expires_at = (now + timedelta(seconds=cooldown_seconds)).isoformat()
    data = {
        "job": job_name,
        "triggered_at": now.isoformat(),
        "cooldown_seconds": cooldown_seconds,
        "expires_at": expires_at,
    }
    _save_cooldown(path, data)
    return data


def clear_cooldown(state_dir: str, job_name: str) -> bool:
    """Remove the cooldown entry for a job. Returns True if it existed."""
    path = _cooldown_path(state_dir, job_name)
    if os.path.exists(path):
        os.remove(path)
        return True
    return False


def is_cooling_down(state_dir: str, job_name: str) -> bool:
    """Return True if the job is still within its cooldown window."""
    path = _cooldown_path(state_dir, job_name)
    data = _load_cooldown(path)
    if not data:
        return False
    expires_at_str = data.get("expires_at")
    if not expires_at_str:
        return False
    expires_at = datetime.fromisoformat(expires_at_str)
    return _utcnow() < expires_at


def cooldown_remaining(state_dir: str, job_name: str) -> Optional[float]:
    """Return seconds remaining in cooldown, or None if not cooling down."""
    path = _cooldown_path(state_dir, job_name)
    data = _load_cooldown(path)
    if not data:
        return None
    expires_at_str = data.get("expires_at")
    if not expires_at_str:
        return None
    expires_at = datetime.fromisoformat(expires_at_str)
    remaining = (expires_at - _utcnow()).total_seconds()
    return remaining if remaining > 0 else None
