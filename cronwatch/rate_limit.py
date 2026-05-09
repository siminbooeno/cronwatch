"""Per-job alert rate limiting based on consecutive failure thresholds."""

from __future__ import annotations

import json
import os
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


@dataclass
class RateLimitState:
    alert_count: int = 0
    first_alert_at: Optional[str] = None
    last_alert_at: Optional[str] = None
    suppressed_count: int = 0


def _rate_limit_path(state_dir: str, job_name: str) -> Path:
    safe = job_name.replace(os.sep, "_").replace(" ", "_")
    return Path(state_dir) / f"{safe}.ratelimit.json"


def _load_state(state_dir: str, job_name: str) -> RateLimitState:
    path = _rate_limit_path(state_dir, job_name)
    if not path.exists():
        return RateLimitState()
    try:
        data = json.loads(path.read_text())
        return RateLimitState(**data)
    except Exception:
        return RateLimitState()


def _save_state(state_dir: str, job_name: str, state: RateLimitState) -> None:
    path = _rate_limit_path(state_dir, job_name)
    Path(state_dir).mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(
            {
                "alert_count": state.alert_count,
                "first_alert_at": state.first_alert_at,
                "last_alert_at": state.last_alert_at,
                "suppressed_count": state.suppressed_count,
            }
        )
    )


def should_send_alert(
    state_dir: str,
    job_name: str,
    max_alerts: int,
    window_seconds: int,
) -> bool:
    """Return True if an alert should be sent for this job.

    Suppresses alerts once ``max_alerts`` have been sent within
    ``window_seconds``.  Resets the window when it expires.
    """
    state = _load_state(state_dir, job_name)
    now = _utcnow()

    if state.first_alert_at is not None:
        first = datetime.fromisoformat(state.first_alert_at)
        elapsed = (now - first).total_seconds()
        if elapsed > window_seconds:
            # Window expired — reset
            state = RateLimitState()

    if state.alert_count >= max_alerts:
        state.suppressed_count += 1
        _save_state(state_dir, job_name, state)
        return False

    now_iso = now.isoformat()
    state.alert_count += 1
    state.last_alert_at = now_iso
    if state.first_alert_at is None:
        state.first_alert_at = now_iso
    _save_state(state_dir, job_name, state)
    return True


def reset_rate_limit(state_dir: str, job_name: str) -> None:
    """Clear rate-limit state for a job (e.g. after it recovers)."""
    path = _rate_limit_path(state_dir, job_name)
    if path.exists():
        path.unlink()
