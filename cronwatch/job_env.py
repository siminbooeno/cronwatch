"""Per-job environment variable management.

Allows storing and retrieving environment variable overrides for jobs,
which are injected at execution time via the runner.
"""
from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Dict, Optional


def _env_path(state_dir: str, job_name: str) -> Path:
    safe = job_name.replace("/", "_").replace(" ", "_")
    return Path(state_dir) / "job_env" / f"{safe}.json"


def _load_env(path: Path) -> Dict[str, str]:
    if not path.exists():
        return {}
    with path.open() as f:
        data = json.load(f)
    return {str(k): str(v) for k, v in data.items()}


def _save_env(path: Path, env: Dict[str, str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w") as f:
        json.dump(env, f, indent=2)


def set_var(state_dir: str, job_name: str, key: str, value: str) -> None:
    """Set an environment variable for a job."""
    path = _env_path(state_dir, job_name)
    env = _load_env(path)
    env[key] = value
    _save_env(path, env)


def unset_var(state_dir: str, job_name: str, key: str) -> bool:
    """Remove an environment variable for a job. Returns True if it existed."""
    path = _env_path(state_dir, job_name)
    env = _load_env(path)
    if key not in env:
        return False
    del env[key]
    _save_env(path, env)
    return True


def get_env(state_dir: str, job_name: str) -> Dict[str, str]:
    """Return all environment variable overrides for a job."""
    return _load_env(_env_path(state_dir, job_name))


def clear_env(state_dir: str, job_name: str) -> int:
    """Remove all environment variable overrides. Returns number removed."""
    path = _env_path(state_dir, job_name)
    env = _load_env(path)
    count = len(env)
    if path.exists():
        path.unlink()
    return count


def build_env(state_dir: str, job_name: str) -> Dict[str, str]:
    """Return a merged env dict: os.environ + job overrides."""
    merged = dict(os.environ)
    merged.update(get_env(state_dir, job_name))
    return merged
