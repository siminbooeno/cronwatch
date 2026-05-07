"""Throttle repeated alerts for the same job to avoid notification spam."""

from __future__ import annotations

import json
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

_THROTTLE_FILE = "alert_throttle.json"


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


def _load_throttle(state_dir: str) -> dict:
    path = Path(state_dir) / _THROTTLE_FILE
    if not path.exists():
        return {}
    with open(path) as f:
        return json.load(f)


def _save_throttle(state_dir: str, data: dict) -> None:
    path = Path(state_dir) / _THROTTLE_FILE
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w") as f:
        json.dump(data, f)


def is_throttled(state_dir: str, job_name: str, cooldown_seconds: int) -> bool:
    """Return True if an alert for *job_name* was sent within *cooldown_seconds*."""
    data = _load_throttle(state_dir)
    last_str: Optional[str] = data.get(job_name)
    if last_str is None:
        return False
    last_dt = datetime.fromisoformat(last_str)
    elapsed = (_utcnow() - last_dt).total_seconds()
    return elapsed < cooldown_seconds


def record_alert_sent(state_dir: str, job_name: str) -> None:
    """Record that an alert was just sent for *job_name*."""
    data = _load_throttle(state_dir)
    data[job_name] = _utcnow().isoformat()
    _save_throttle(state_dir, data)


def clear_throttle(state_dir: str, job_name: str) -> None:
    """Remove throttle entry for *job_name* (e.g. after a successful run)."""
    data = _load_throttle(state_dir)
    data.pop(job_name, None)
    _save_throttle(state_dir, data)


def prune_throttle(state_dir: str, max_age_seconds: int = 86400) -> int:
    """Remove stale throttle entries older than *max_age_seconds*. Returns count removed."""
    data = _load_throttle(state_dir)
    now = _utcnow()
    stale = [
        k for k, v in data.items()
        if (now - datetime.fromisoformat(v)).total_seconds() > max_age_seconds
    ]
    for key in stale:
        del data[key]
    _save_throttle(state_dir, data)
    return len(stale)
