"""On-call schedule support: map jobs to on-call contacts for targeted alerting."""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List, Optional


@dataclass
class OncallEntry:
    contact: str  # email or webhook URL
    jobs: List[str] = field(default_factory=list)  # empty = applies to all jobs
    tags: List[str] = field(default_factory=list)  # match jobs with these tags
    note: str = ""


def _oncall_path(state_dir: str) -> Path:
    return Path(state_dir) / "oncall.json"


def _load_oncall(state_dir: str) -> List[dict]:
    p = _oncall_path(state_dir)
    if not p.exists():
        return []
    with p.open() as fh:
        return json.load(fh)


def _save_oncall(state_dir: str, entries: List[dict]) -> None:
    p = _oncall_path(state_dir)
    p.parent.mkdir(parents=True, exist_ok=True)
    with p.open("w") as fh:
        json.dump(entries, fh, indent=2)


def set_oncall(state_dir: str, contact: str, jobs: Optional[List[str]] = None,
               tags: Optional[List[str]] = None, note: str = "") -> OncallEntry:
    """Add or replace an on-call entry for a contact."""
    entries = _load_oncall(state_dir)
    entries = [e for e in entries if e["contact"] != contact]
    entry = {
        "contact": contact,
        "jobs": jobs or [],
        "tags": tags or [],
        "note": note,
    }
    entries.append(entry)
    _save_oncall(state_dir, entries)
    return OncallEntry(**entry)


def remove_oncall(state_dir: str, contact: str) -> bool:
    """Remove an on-call entry. Returns True if it existed."""
    entries = _load_oncall(state_dir)
    new = [e for e in entries if e["contact"] != contact]
    if len(new) == len(entries):
        return False
    _save_oncall(state_dir, new)
    return True


def get_oncall_contacts(state_dir: str, job_name: str,
                        job_tags: Optional[List[str]] = None) -> List[str]:
    """Return contacts that should be notified for a given job."""
    entries = _load_oncall(state_dir)
    job_tags = job_tags or []
    contacts: List[str] = []
    for e in entries:
        job_list: List[str] = e.get("jobs", [])
        tag_list: List[str] = e.get("tags", [])
        # global entry (no job/tag filter)
        if not job_list and not tag_list:
            contacts.append(e["contact"])
            continue
        if job_name in job_list:
            contacts.append(e["contact"])
            continue
        if tag_list and any(t in job_tags for t in tag_list):
            contacts.append(e["contact"])
    return contacts


def list_oncall(state_dir: str) -> List[OncallEntry]:
    """Return all on-call entries."""
    return [OncallEntry(**e) for e in _load_oncall(state_dir)]
