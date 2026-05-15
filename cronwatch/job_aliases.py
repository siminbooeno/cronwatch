"""Job alias management — map short aliases to canonical job names."""
from __future__ import annotations

import json
import os
from typing import Dict, List, Optional


def _aliases_path(state_dir: str) -> str:
    return os.path.join(state_dir, "job_aliases.json")


def _load_aliases(state_dir: str) -> Dict[str, str]:
    path = _aliases_path(state_dir)
    if not os.path.exists(path):
        return {}
    with open(path) as f:
        return json.load(f)


def _save_aliases(state_dir: str, data: Dict[str, str]) -> None:
    os.makedirs(state_dir, exist_ok=True)
    with open(_aliases_path(state_dir), "w") as f:
        json.dump(data, f, indent=2)


def set_alias(state_dir: str, alias: str, job_name: str) -> None:
    """Create or overwrite an alias pointing to job_name."""
    data = _load_aliases(state_dir)
    data[alias] = job_name
    _save_aliases(state_dir, data)


def remove_alias(state_dir: str, alias: str) -> bool:
    """Remove an alias. Returns True if it existed, False otherwise."""
    data = _load_aliases(state_dir)
    if alias not in data:
        return False
    del data[alias]
    _save_aliases(state_dir, data)
    return True


def resolve_alias(state_dir: str, alias: str) -> Optional[str]:
    """Return the job name for the given alias, or None if not found."""
    return _load_aliases(state_dir).get(alias)


def list_aliases(state_dir: str) -> Dict[str, str]:
    """Return all alias -> job_name mappings."""
    return dict(_load_aliases(state_dir))


def aliases_for_job(state_dir: str, job_name: str) -> List[str]:
    """Return all aliases that point to job_name."""
    return [alias for alias, target in _load_aliases(state_dir).items() if target == job_name]
