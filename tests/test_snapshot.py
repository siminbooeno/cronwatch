"""Tests for cronwatch.snapshot."""

from __future__ import annotations

import json
import os
from datetime import datetime, timezone

import pytest

from cronwatch.config import CronwatchConfig, JobConfig, AlertConfig
from cronwatch.snapshot import (
    JobSnapshot,
    Snapshot,
    capture_snapshot,
    diff_snapshots,
    load_snapshot,
    save_snapshot,
)


@pytest.fixture()
def dirs(tmp_path):
    return {
        "state": str(tmp_path / "state"),
        "history": str(tmp_path / "history"),
        "snapshots": str(tmp_path / "snapshots"),
    }


def _make_cfg(*names: str) -> CronwatchConfig:
    jobs = [
        JobConfig(name=n, command="echo hi", interval=60, tags=["web"])
        for n in names
    ]
    alert = AlertConfig(webhook_url=None, email=None)
    return CronwatchConfig(jobs=jobs, alert=alert, state_dir="/tmp", history_dir="/tmp")


def test_capture_snapshot_returns_snapshot(dirs):
    cfg = _make_cfg("backup", "cleanup")
    snap = capture_snapshot(cfg, dirs["state"], dirs["history"])
    assert isinstance(snap, Snapshot)
    assert len(snap.jobs) == 2
    assert snap.captured_at  # non-empty ISO string


def test_capture_snapshot_no_history(dirs):
    cfg = _make_cfg("myjob")
    snap = capture_snapshot(cfg, dirs["state"], dirs["history"])
    job = snap.jobs[0]
    assert job.job_name == "myjob"
    assert job.last_seen is None
    assert job.success_rate == 0.0
    assert job.consecutive_failures == 0


def test_save_and_load_snapshot(dirs):
    snap = Snapshot(
        captured_at="2024-01-01T00:00:00+00:00",
        jobs=[
            JobSnapshot(
                job_name="foo",
                last_seen="2024-01-01T00:00:00+00:00",
                success_rate=1.0,
                consecutive_failures=0,
                tags=["web"],
            )
        ],
    )
    path = os.path.join(dirs["snapshots"], "snap.json")
    save_snapshot(snap, path)
    loaded = load_snapshot(path)
    assert loaded is not None
    assert loaded.captured_at == snap.captured_at
    assert len(loaded.jobs) == 1
    assert loaded.jobs[0].job_name == "foo"
    assert loaded.jobs[0].success_rate == 1.0


def test_load_snapshot_missing_returns_none(dirs):
    path = os.path.join(dirs["snapshots"], "nonexistent.json")
    assert load_snapshot(path) is None


def test_diff_snapshots_detects_changes():
    prev = Snapshot(
        captured_at="2024-01-01T00:00:00+00:00",
        jobs=[JobSnapshot("jobA", None, 1.0, 0, [])],
    )
    curr = Snapshot(
        captured_at="2024-01-02T00:00:00+00:00",
        jobs=[JobSnapshot("jobA", "2024-01-02T00:00:00+00:00", 0.5, 3, [])],
    )
    changes = diff_snapshots(prev, curr)
    assert "jobA" in changes
    assert "last_seen" in changes["jobA"]
    assert "success_rate" in changes["jobA"]
    assert "consecutive_failures" in changes["jobA"]


def test_diff_snapshots_no_changes():
    job = JobSnapshot("jobB", "2024-01-01T00:00:00+00:00", 1.0, 0, [])
    prev = Snapshot(captured_at="2024-01-01T00:00:00+00:00", jobs=[job])
    curr = Snapshot(captured_at="2024-01-02T00:00:00+00:00", jobs=[job])
    changes = diff_snapshots(prev, curr)
    assert changes == {}


def test_diff_snapshots_new_job():
    prev = Snapshot(captured_at="2024-01-01T00:00:00+00:00", jobs=[])
    curr = Snapshot(
        captured_at="2024-01-02T00:00:00+00:00",
        jobs=[JobSnapshot("newjob", None, 0.0, 0, [])],
    )
    changes = diff_snapshots(prev, curr)
    assert "newjob" in changes
    assert changes["newjob"] == {"new": True}
