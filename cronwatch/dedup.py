"""Alert deduplication: suppress repeated alerts for the same job+event
within a configurable time window."""

from __future__ import annotations

import json
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

_DEDUP_FILENAME = "dedup.json"


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


def _dedup_path(state_dir: str) -> Path:
    return Path(state_dir) / _DEDUP_FILENAME


def _load_dedup(state_dir: str) -> dict:
    path = _dedup_path(state_dir)
    if not path.exists():
        return {}
    try:
        return json.loads(path.read_text())
    except (json.JSONDecodeError, OSError):
        return {}


def _save_dedup(state_dir: str, data: dict) -> None:
    path = _dedup_path(state_dir)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2))


def _dedup_key(job_name: str, event_type: str) -> str:
    return f"{job_name}::{event_type}"


def is_duplicate(state_dir: str, job_name: str, event_type: str, window_seconds: int) -> bool:
    """Return True if an identical alert was already sent within *window_seconds*."""
    data = _load_dedup(state_dir)
    key = _dedup_key(job_name, event_type)
    entry = data.get(key)
    if entry is None:
        return False
    try:
        last_sent = datetime.fromisoformat(entry["last_sent"])
    except (KeyError, ValueError):
        return False
    elapsed = (_utcnow() - last_sent).total_seconds()
    return elapsed < window_seconds


def record_alert_dedup(state_dir: str, job_name: str, event_type: str) -> None:
    """Record that an alert of *event_type* was sent for *job_name* right now."""
    data = _load_dedup(state_dir)
    key = _dedup_key(job_name, event_type)
    data[key] = {"last_sent": _utcnow().isoformat(), "job": job_name, "event": event_type}
    _save_dedup(state_dir, data)


def clear_dedup(state_dir: str, job_name: str, event_type: Optional[str] = None) -> None:
    """Clear dedup entries for a job (optionally scoped to one event type)."""
    data = _load_dedup(state_dir)
    if event_type is not None:
        data.pop(_dedup_key(job_name, event_type), None)
    else:
        keys_to_remove = [k for k in data if k.startswith(f"{job_name}::")]
        for k in keys_to_remove:
            del data[k]
    _save_dedup(state_dir, data)
