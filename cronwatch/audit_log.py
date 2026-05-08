"""Append-only audit log for cronwatch events (alerts sent, jobs run, etc.)."""

from __future__ import annotations

import json
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional


AUDIT_LOG_FILENAME = "audit.jsonl"


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


def _audit_log_path(state_dir: str) -> Path:
    return Path(state_dir) / AUDIT_LOG_FILENAME


def append_event(
    state_dir: str,
    event_type: str,
    job_name: Optional[str] = None,
    details: Optional[Dict[str, Any]] = None,
) -> None:
    """Append a single audit event to the JSONL audit log."""
    record: Dict[str, Any] = {
        "ts": _utcnow().isoformat(),
        "event": event_type,
    }
    if job_name is not None:
        record["job"] = job_name
    if details:
        record["details"] = details

    log_path = _audit_log_path(state_dir)
    os.makedirs(state_dir, exist_ok=True)
    with open(log_path, "a", encoding="utf-8") as fh:
        fh.write(json.dumps(record) + "\n")


def read_events(
    state_dir: str,
    event_type: Optional[str] = None,
    job_name: Optional[str] = None,
    limit: Optional[int] = None,
) -> List[Dict[str, Any]]:
    """Read audit events, optionally filtered by event_type and/or job_name."""
    log_path = _audit_log_path(state_dir)
    if not log_path.exists():
        return []

    results: List[Dict[str, Any]] = []
    with open(log_path, "r", encoding="utf-8") as fh:
        for line in fh:
            line = line.strip()
            if not line:
                continue
            try:
                record = json.loads(line)
            except json.JSONDecodeError:
                continue
            if event_type and record.get("event") != event_type:
                continue
            if job_name and record.get("job") != job_name:
                continue
            results.append(record)

    if limit is not None:
        results = results[-limit:]
    return results


def prune_audit_log(state_dir: str, keep_days: int = 30) -> int:
    """Remove audit entries older than keep_days. Returns number of removed entries."""
    log_path = _audit_log_path(state_dir)
    if not log_path.exists():
        return 0

    cutoff = _utcnow().replace(tzinfo=timezone.utc)
    kept: List[str] = []
    removed = 0

    with open(log_path, "r", encoding="utf-8") as fh:
        for line in fh:
            stripped = line.strip()
            if not stripped:
                continue
            try:
                record = json.loads(stripped)
                ts = datetime.fromisoformat(record["ts"])
                if ts.tzinfo is None:
                    ts = ts.replace(tzinfo=timezone.utc)
                age_days = (cutoff - ts).total_seconds() / 86400
                if age_days <= keep_days:
                    kept.append(stripped)
                else:
                    removed += 1
            except (json.JSONDecodeError, KeyError, ValueError):
                kept.append(stripped)

    with open(log_path, "w", encoding="utf-8") as fh:
        fh.write("\n".join(kept) + ("\n" if kept else ""))

    return removed
