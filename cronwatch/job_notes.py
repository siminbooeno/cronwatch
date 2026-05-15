"""Per-job freeform notes store — attach, list, and delete notes on jobs."""
from __future__ import annotations

import json
import os
import uuid
from datetime import datetime, timezone
from typing import List, Optional


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


def _notes_path(state_dir: str, job_name: str) -> str:
    safe = job_name.replace(os.sep, "_")
    return os.path.join(state_dir, f"notes_{safe}.json")


def _load_notes(path: str) -> List[dict]:
    if not os.path.exists(path):
        return []
    with open(path) as fh:
        return json.load(fh)


def _save_notes(path: str, notes: List[dict]) -> None:
    os.makedirs(os.path.dirname(path) or ".", exist_ok=True)
    with open(path, "w") as fh:
        json.dump(notes, fh, indent=2)


def add_note(
    state_dir: str,
    job_name: str,
    text: str,
    author: Optional[str] = None,
) -> dict:
    """Append a note to the job and return the created record."""
    path = _notes_path(state_dir, job_name)
    notes = _load_notes(path)
    record = {
        "id": str(uuid.uuid4()),
        "job": job_name,
        "text": text,
        "author": author,
        "created_at": _utcnow().isoformat(),
    }
    notes.append(record)
    _save_notes(path, notes)
    return record


def get_notes(state_dir: str, job_name: str) -> List[dict]:
    """Return all notes for a job, oldest first."""
    return _load_notes(_notes_path(state_dir, job_name))


def delete_note(state_dir: str, job_name: str, note_id: str) -> bool:
    """Delete a note by id. Returns True if found and removed."""
    path = _notes_path(state_dir, job_name)
    notes = _load_notes(path)
    new_notes = [n for n in notes if n["id"] != note_id]
    if len(new_notes) == len(notes):
        return False
    _save_notes(path, new_notes)
    return True


def clear_notes(state_dir: str, job_name: str) -> int:
    """Remove all notes for a job. Returns count deleted."""
    path = _notes_path(state_dir, job_name)
    notes = _load_notes(path)
    count = len(notes)
    if count:
        _save_notes(path, [])
    return count
