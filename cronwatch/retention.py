"""Retention policy: prune old history and state entries."""

from __future__ import annotations

import json
import os
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Optional


def _utcnow() -> datetime:
    return datetime.now(tz=timezone.utc)


def prune_history(history_dir: str | Path, max_age_days: int, job_name: str) -> int:
    """Remove execution records older than *max_age_days* for *job_name*.

    Returns the number of records removed.
    """
    history_dir = Path(history_dir)
    history_file = history_dir / f"{job_name}.json"
    if not history_file.exists():
        return 0

    cutoff = _utcnow() - timedelta(days=max_age_days)

    with history_file.open() as fh:
        records: list[dict] = json.load(fh)

    before = len(records)
    kept = [
        r for r in records
        if datetime.fromisoformat(r["timestamp"]) >= cutoff
    ]
    removed = before - len(kept)

    if removed:
        with history_file.open("w") as fh:
            json.dump(kept, fh, indent=2)

    return removed


def prune_all_history(
    history_dir: str | Path,
    max_age_days: int,
    job_names: Optional[list[str]] = None,
) -> dict[str, int]:
    """Prune history for all known jobs (or a specific list).

    Returns a mapping of job_name -> records_removed.
    """
    history_dir = Path(history_dir)
    if job_names is None:
        job_names = [
            p.stem for p in history_dir.glob("*.json")
        ]

    results: dict[str, int] = {}
    for name in job_names:
        results[name] = prune_history(history_dir, max_age_days, name)
    return results


def prune_state(
    state_dir: str | Path,
    max_age_days: int,
    job_name: str,
) -> bool:
    """Clear state for *job_name* if last_seen is older than *max_age_days*.

    Returns True if the state file was removed, False otherwise.
    """
    state_dir = Path(state_dir)
    state_file = state_dir / f"{job_name}.json"
    if not state_file.exists():
        return False

    with state_file.open() as fh:
        state: dict = json.load(fh)

    last_seen = state.get("last_seen")
    if last_seen is None:
        return False

    cutoff = _utcnow() - timedelta(days=max_age_days)
    if datetime.fromisoformat(last_seen) < cutoff:
        state_file.unlink()
        return True

    return False
