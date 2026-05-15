"""Job ownership tracking — assign owners (team/person) to jobs."""
from __future__ import annotations

import json
import os
from datetime import datetime, timezone
from typing import Dict, List, Optional


def _utcnow() -> str:
    return datetime.now(timezone.utc).isoformat()


def _ownership_path(state_dir: str) -> str:
    return os.path.join(state_dir, "job_ownership.json")


def _load_ownership(state_dir: str) -> Dict[str, dict]:
    path = _ownership_path(state_dir)
    if not os.path.exists(path):
        return {}
    with open(path) as f:
        return json.load(f)


def _save_ownership(state_dir: str, data: Dict[str, dict]) -> None:
    os.makedirs(state_dir, exist_ok=True)
    with open(_ownership_path(state_dir), "w") as f:
        json.dump(data, f, indent=2)


def set_owner(state_dir: str, job_name: str, owner: str, email: Optional[str] = None, team: Optional[str] = None) -> dict:
    """Assign an owner to a job. Returns the ownership record."""
    data = _load_ownership(state_dir)
    record = {
        "job": job_name,
        "owner": owner,
        "email": email,
        "team": team,
        "assigned_at": _utcnow(),
    }
    data[job_name] = record
    _save_ownership(state_dir, data)
    return record


def remove_owner(state_dir: str, job_name: str) -> bool:
    """Remove ownership for a job. Returns True if removed, False if not found."""
    data = _load_ownership(state_dir)
    if job_name not in data:
        return False
    del data[job_name]
    _save_ownership(state_dir, data)
    return True


def get_owner(state_dir: str, job_name: str) -> Optional[dict]:
    """Return ownership record for a job, or None."""
    return _load_ownership(state_dir).get(job_name)


def list_owners(state_dir: str) -> List[dict]:
    """Return all ownership records sorted by job name."""
    data = _load_ownership(state_dir)
    return sorted(data.values(), key=lambda r: r["job"])


def jobs_owned_by(state_dir: str, owner: str) -> List[dict]:
    """Return all ownership records where owner matches (case-insensitive)."""
    return [
        r for r in list_owners(state_dir)
        if r["owner"].lower() == owner.lower()
    ]


def jobs_owned_by_team(state_dir: str, team: str) -> List[dict]:
    """Return all ownership records where team matches (case-insensitive)."""
    return [
        r for r in list_owners(state_dir)
        if r.get("team", "") and r["team"].lower() == team.lower()
    ]
