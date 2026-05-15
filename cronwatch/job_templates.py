"""Job template management: define reusable job config templates."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, List, Optional


def _templates_path(state_dir: str) -> Path:
    return Path(state_dir) / "job_templates.json"


def _load_templates(state_dir: str) -> Dict[str, Dict[str, Any]]:
    path = _templates_path(state_dir)
    if not path.exists():
        return {}
    with path.open() as f:
        return json.load(f)


def _save_templates(state_dir: str, data: Dict[str, Dict[str, Any]]) -> None:
    path = _templates_path(state_dir)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w") as f:
        json.dump(data, f, indent=2)


def set_template(state_dir: str, name: str, defaults: Dict[str, Any]) -> Dict[str, Any]:
    """Create or overwrite a named job template."""
    data = _load_templates(state_dir)
    record = {"name": name, "defaults": defaults}
    data[name] = record
    _save_templates(state_dir, data)
    return record


def get_template(state_dir: str, name: str) -> Optional[Dict[str, Any]]:
    """Return the template record for *name*, or None if not found."""
    data = _load_templates(state_dir)
    return data.get(name)


def delete_template(state_dir: str, name: str) -> bool:
    """Delete a template by name. Returns True if it existed."""
    data = _load_templates(state_dir)
    if name not in data:
        return False
    del data[name]
    _save_templates(state_dir, data)
    return True


def list_templates(state_dir: str) -> List[Dict[str, Any]]:
    """Return all templates sorted by name."""
    data = _load_templates(state_dir)
    return sorted(data.values(), key=lambda r: r["name"])


def apply_template(
    state_dir: str, name: str, overrides: Dict[str, Any]
) -> Dict[str, Any]:
    """Merge template defaults with *overrides* and return the result.

    Raises KeyError if the template does not exist.
    """
    record = get_template(state_dir, name)
    if record is None:
        raise KeyError(f"Template '{name}' not found")
    merged = dict(record["defaults"])
    merged.update(overrides)
    return merged
