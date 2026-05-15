"""Arbitrary key-value metadata storage for jobs."""

from __future__ import annotations

import json
import os
from typing import Dict, Optional


def _metadata_path(state_dir: str, job_name: str) -> str:
    safe = job_name.replace("/", "_").replace(" ", "_")
    return os.path.join(state_dir, f"{safe}.metadata.json")


def _load_metadata(path: str) -> Dict[str, str]:
    if not os.path.exists(path):
        return {}
    with open(path, "r") as fh:
        return json.load(fh)


def _save_metadata(path: str, data: Dict[str, str]) -> None:
    os.makedirs(os.path.dirname(path) or ".", exist_ok=True)
    with open(path, "w") as fh:
        json.dump(data, fh, indent=2)


def set_metadata(state_dir: str, job_name: str, key: str, value: str) -> Dict[str, str]:
    """Set a metadata key for a job. Returns the updated metadata dict."""
    path = _metadata_path(state_dir, job_name)
    data = _load_metadata(path)
    data[key] = value
    _save_metadata(path, data)
    return data


def unset_metadata(state_dir: str, job_name: str, key: str) -> bool:
    """Remove a metadata key. Returns True if the key existed."""
    path = _metadata_path(state_dir, job_name)
    data = _load_metadata(path)
    if key not in data:
        return False
    del data[key]
    _save_metadata(path, data)
    return True


def get_metadata(state_dir: str, job_name: str) -> Dict[str, str]:
    """Return all metadata for a job."""
    path = _metadata_path(state_dir, job_name)
    return _load_metadata(path)


def get_value(state_dir: str, job_name: str, key: str) -> Optional[str]:
    """Return a single metadata value, or None if not set."""
    return get_metadata(state_dir, job_name).get(key)


def clear_metadata(state_dir: str, job_name: str) -> int:
    """Delete all metadata for a job. Returns the number of keys removed."""
    path = _metadata_path(state_dir, job_name)
    data = _load_metadata(path)
    count = len(data)
    if count and os.path.exists(path):
        os.remove(path)
    return count
