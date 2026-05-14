"""Job annotations: attach arbitrary key-value metadata to job execution records."""
from __future__ import annotations

import json
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


def _annotations_path(state_dir: str, job_name: str) -> Path:
    safe = job_name.replace(os.sep, "_")
    return Path(state_dir) / f"{safe}.annotations.json"


def _load_annotations(path: Path) -> List[Dict[str, Any]]:
    if not path.exists():
        return []
    try:
        return json.loads(path.read_text())
    except (json.JSONDecodeError, OSError):
        return []


def _save_annotations(path: Path, records: List[Dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(records, indent=2))


def add_annotation(
    state_dir: str,
    job_name: str,
    key: str,
    value: Any,
    *,
    author: Optional[str] = None,
) -> Dict[str, Any]:
    """Append a key/value annotation for *job_name* and return the new record."""
    path = _annotations_path(state_dir, job_name)
    records = _load_annotations(path)
    record: Dict[str, Any] = {
        "ts": _utcnow().isoformat(),
        "key": key,
        "value": value,
    }
    if author:
        record["author"] = author
    records.append(record)
    _save_annotations(path, records)
    return record


def get_annotations(
    state_dir: str,
    job_name: str,
    *,
    key: Optional[str] = None,
) -> List[Dict[str, Any]]:
    """Return all annotations for *job_name*, optionally filtered by *key*."""
    path = _annotations_path(state_dir, job_name)
    records = _load_annotations(path)
    if key is not None:
        records = [r for r in records if r.get("key") == key]
    return records


def delete_annotations(
    state_dir: str,
    job_name: str,
    *,
    key: Optional[str] = None,
) -> int:
    """Delete annotations for *job_name*.  If *key* is given, only that key.
    Returns the number of records removed."""
    path = _annotations_path(state_dir, job_name)
    records = _load_annotations(path)
    if key is None:
        removed = len(records)
        _save_annotations(path, [])
        return removed
    kept = [r for r in records if r.get("key") != key]
    removed = len(records) - len(kept)
    _save_annotations(path, kept)
    return removed
