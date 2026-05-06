"""Tests for cronwatch.retention."""

from __future__ import annotations

import json
from datetime import datetime, timedelta, timezone
from pathlib import Path

import pytest

from cronwatch.retention import prune_history, prune_all_history, prune_state


def _iso(dt: datetime) -> str:
    return dt.isoformat()


def _utcnow() -> datetime:
    return datetime.now(tz=timezone.utc)


@pytest.fixture()
def history_dir(tmp_path: Path) -> Path:
    d = tmp_path / "history"
    d.mkdir()
    return d


@pytest.fixture()
def state_dir(tmp_path: Path) -> Path:
    d = tmp_path / "state"
    d.mkdir()
    return d


def _write_history(history_dir: Path, job: str, records: list[dict]) -> None:
    (history_dir / f"{job}.json").write_text(json.dumps(records, indent=2))


def _write_state(state_dir: Path, job: str, last_seen: str | None) -> None:
    data = {"last_seen": last_seen, "consecutive_failures": 0}
    (state_dir / f"{job}.json").write_text(json.dumps(data))


# --- prune_history ---

def test_prune_history_removes_old_records(history_dir: Path) -> None:
    now = _utcnow()
    records = [
        {"timestamp": _iso(now - timedelta(days=10)), "success": True},
        {"timestamp": _iso(now - timedelta(days=2)), "success": True},
        {"timestamp": _iso(now - timedelta(hours=1)), "success": False},
    ]
    _write_history(history_dir, "myjob", records)

    removed = prune_history(history_dir, max_age_days=7, job_name="myjob")

    assert removed == 1
    kept = json.loads((history_dir / "myjob.json").read_text())
    assert len(kept) == 2


def test_prune_history_no_file_returns_zero(history_dir: Path) -> None:
    assert prune_history(history_dir, max_age_days=7, job_name="ghost") == 0


def test_prune_history_all_recent_no_removal(history_dir: Path) -> None:
    now = _utcnow()
    records = [{"timestamp": _iso(now - timedelta(hours=3)), "success": True}]
    _write_history(history_dir, "myjob", records)

    removed = prune_history(history_dir, max_age_days=7, job_name="myjob")
    assert removed == 0


# --- prune_all_history ---

def test_prune_all_history_multiple_jobs(history_dir: Path) -> None:
    now = _utcnow()
    old = {"timestamp": _iso(now - timedelta(days=20)), "success": True}
    recent = {"timestamp": _iso(now - timedelta(hours=1)), "success": True}

    _write_history(history_dir, "job_a", [old, recent])
    _write_history(history_dir, "job_b", [old])

    results = prune_all_history(history_dir, max_age_days=7)

    assert results["job_a"] == 1
    assert results["job_b"] == 1


def test_prune_all_history_respects_job_names_filter(history_dir: Path) -> None:
    now = _utcnow()
    old = {"timestamp": _iso(now - timedelta(days=20)), "success": True}
    _write_history(history_dir, "job_a", [old])
    _write_history(history_dir, "job_b", [old])

    results = prune_all_history(history_dir, max_age_days=7, job_names=["job_a"])
    assert "job_b" not in results
    assert results["job_a"] == 1


# --- prune_state ---

def test_prune_state_removes_stale_state(state_dir: Path) -> None:
    old_ts = _iso(_utcnow() - timedelta(days=30))
    _write_state(state_dir, "myjob", old_ts)

    removed = prune_state(state_dir, max_age_days=7, job_name="myjob")
    assert removed is True
    assert not (state_dir / "myjob.json").exists()


def test_prune_state_keeps_recent_state(state_dir: Path) -> None:
    recent_ts = _iso(_utcnow() - timedelta(hours=2))
    _write_state(state_dir, "myjob", recent_ts)

    removed = prune_state(state_dir, max_age_days=7, job_name="myjob")
    assert removed is False
    assert (state_dir / "myjob.json").exists()


def test_prune_state_no_file_returns_false(state_dir: Path) -> None:
    assert prune_state(state_dir, max_age_days=7, job_name="ghost") is False
