"""Runbook links: attach documentation URLs to jobs for alert enrichment."""

from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Dict, List, Optional


def _runbooks_path(state_dir: str) -> Path:
    return Path(state_dir) / "runbooks.json"


def _load_runbooks(state_dir: str) -> Dict[str, str]:
    path = _runbooks_path(state_dir)
    if not path.exists():
        return {}
    with path.open() as fh:
        return json.load(fh)


def _save_runbooks(state_dir: str, data: Dict[str, str]) -> None:
    path = _runbooks_path(state_dir)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w") as fh:
        json.dump(data, fh, indent=2)


def set_runbook(state_dir: str, job_name: str, url: str) -> None:
    """Associate a runbook URL with a job."""
    data = _load_runbooks(state_dir)
    data[job_name] = url
    _save_runbooks(state_dir, data)


def get_runbook(state_dir: str, job_name: str) -> Optional[str]:
    """Return the runbook URL for a job, or None if not set."""
    return _load_runbooks(state_dir).get(job_name)


def delete_runbook(state_dir: str, job_name: str) -> bool:
    """Remove a runbook link. Returns True if it existed."""
    data = _load_runbooks(state_dir)
    if job_name not in data:
        return False
    del data[job_name]
    _save_runbooks(state_dir, data)
    return True


def list_runbooks(state_dir: str) -> List[Dict[str, str]]:
    """Return all runbook entries as a list of dicts."""
    data = _load_runbooks(state_dir)
    return [{"job": k, "url": v} for k, v in sorted(data.items())]


def enrich_alert_message(state_dir: str, job_name: str, message: str) -> str:
    """Append runbook URL to an alert message if one is configured."""
    url = get_runbook(state_dir, job_name)
    if url:
        return f"{message}\nRunbook: {url}"
    return message
