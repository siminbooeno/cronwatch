"""Tests for cronwatch.dependencies."""

from __future__ import annotations

import json
import os
import time
from pathlib import Path
from unittest.mock import patch

import pytest

from cronwatch.config import JobConfig, CronwatchConfig, AlertConfig
from cronwatch.dependencies import (
    check_dependencies,
    filter_ready_jobs,
    _last_success_within,
)


@pytest.fixture()
def history_dir(tmp_path: Path) -> str:
    return str(tmp_path)


def _make_job(name: str, depends_on=None, interval: int = 3600) -> JobConfig:
    return JobConfig(
        name=name,
        command=f"echo {name}",
        interval_seconds=interval,
        grace_seconds=60,
        depends_on=depends_on or [],
    )


def _make_config(*jobs: JobConfig) -> CronwatchConfig:
    alert = AlertConfig(webhook_url=None, email_to=None, email_from=None, smtp_host=None)
    return CronwatchConfig(jobs=list(jobs), alert=alert, state_dir="/tmp")


def _write_success(history_dir: str, job_name: str, ago_seconds: float = 0) -> None:
    """Write a fake success record for job_name."""
    job_dir = os.path.join(history_dir, job_name)
    os.makedirs(job_dir, exist_ok=True)
    ts = time.time() - ago_seconds
    record = {"timestamp": ts, "success": True, "duration": 1.0, "exit_code": 0}
    path = os.path.join(job_dir, f"{int(ts)}.json")
    with open(path, "w") as f:
        json.dump(record, f)


def test_no_deps_always_satisfied(history_dir):
    job = _make_job("backup")
    cfg = _make_config(job)
    result = check_dependencies(job, cfg, history_dir)
    assert result.satisfied is True
    assert result.blocking_deps == []


def test_dep_never_ran_blocks(history_dir):
    dep = _make_job("setup")
    job = _make_job("backup", depends_on=["setup"])
    cfg = _make_config(dep, job)
    result = check_dependencies(job, cfg, history_dir)
    assert result.satisfied is False
    assert "setup" in result.blocking_deps


def test_dep_ran_recently_satisfied(history_dir):
    dep = _make_job("setup", interval=3600)
    job = _make_job("backup", depends_on=["setup"])
    cfg = _make_config(dep, job)
    _write_success(history_dir, "setup", ago_seconds=100)
    result = check_dependencies(job, cfg, history_dir)
    assert result.satisfied is True


def test_dep_ran_too_long_ago_blocks(history_dir):
    dep = _make_job("setup", interval=60)
    job = _make_job("backup", depends_on=["setup"])
    cfg = _make_config(dep, job)
    _write_success(history_dir, "setup", ago_seconds=200)  # interval+grace = 120
    result = check_dependencies(job, cfg, history_dir)
    assert result.satisfied is False


def test_unknown_dep_blocks(history_dir):
    job = _make_job("backup", depends_on=["ghost"])
    cfg = _make_config(job)
    result = check_dependencies(job, cfg, history_dir)
    assert result.satisfied is False
    assert "ghost" in result.blocking_deps


def test_filter_ready_excludes_blocked(history_dir):
    dep = _make_job("setup")
    job = _make_job("backup", depends_on=["setup"])
    standalone = _make_job("report")
    cfg = _make_config(dep, job, standalone)
    ready = filter_ready_jobs([dep, job, standalone], cfg, history_dir)
    names = [j.name for j in ready]
    assert "backup" not in names
    assert "setup" in names
    assert "report" in names
