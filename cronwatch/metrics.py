"""Lightweight in-process metrics collection for cronwatch."""
from __future__ import annotations

import json
import time
from pathlib import Path
from typing import Dict, Any


def _utcnow() -> float:
    return time.time()


def _metrics_path(state_dir: str) -> Path:
    return Path(state_dir) / "metrics.json"


def _load_metrics(state_dir: str) -> Dict[str, Any]:
    p = _metrics_path(state_dir)
    if not p.exists():
        return {}
    try:
        return json.loads(p.read_text())
    except (json.JSONDecodeError, OSError):
        return {}


def _save_metrics(state_dir: str, data: Dict[str, Any]) -> None:
    p = _metrics_path(state_dir)
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps(data, indent=2))


def increment(state_dir: str, key: str, amount: int = 1) -> None:
    """Increment a named counter by *amount*."""
    data = _load_metrics(state_dir)
    counters = data.setdefault("counters", {})
    counters[key] = counters.get(key, 0) + amount
    data["updated_at"] = _utcnow()
    _save_metrics(state_dir, data)


def get_counter(state_dir: str, key: str) -> int:
    """Return current value of a named counter (0 if not set)."""
    data = _load_metrics(state_dir)
    return data.get("counters", {}).get(key, 0)


def reset_counter(state_dir: str, key: str) -> None:
    """Reset a named counter to zero."""
    data = _load_metrics(state_dir)
    data.setdefault("counters", {})[key] = 0
    data["updated_at"] = _utcnow()
    _save_metrics(state_dir, data)


def all_counters(state_dir: str) -> Dict[str, int]:
    """Return a snapshot of all counters."""
    data = _load_metrics(state_dir)
    return dict(data.get("counters", {}))


def record_job_run(state_dir: str, job_name: str, success: bool) -> None:
    """Convenience: increment per-job run/success/failure counters."""
    increment(state_dir, f"job.{job_name}.runs")
    if success:
        increment(state_dir, f"job.{job_name}.successes")
    else:
        increment(state_dir, f"job.{job_name}.failures")
    increment(state_dir, "total.runs")
    if not success:
        increment(state_dir, "total.failures")
