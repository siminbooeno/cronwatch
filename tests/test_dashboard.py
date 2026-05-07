"""Tests for cronwatch.dashboard and cronwatch.cli_dashboard."""

from __future__ import annotations

import json
import os
import pathlib

import pytest

from cronwatch.config import load_config
from cronwatch.dashboard import JobRow, build_dashboard, render_text
from cronwatch.history import JobHistory
from cronwatch.state import record_success, record_failure


@pytest.fixture()
def dirs(tmp_path: pathlib.Path):
    state = tmp_path / "state"
    history = tmp_path / "history"
    state.mkdir()
    history.mkdir()
    return str(state), str(history)


@pytest.fixture()
def config_file(tmp_path: pathlib.Path):
    cfg = {
        "jobs": [
            {"name": "backup", "interval_seconds": 3600, "grace_seconds": 60},
            {"name": "cleanup", "interval_seconds": 86400, "grace_seconds": 300},
        ],
        "alert": {"webhook_url": "http://example.com/hook"},
    }
    p = tmp_path / "config.json"
    p.write_text(json.dumps(cfg))
    return str(p)


def test_build_dashboard_no_history(config_file, dirs):
    state_dir, history_dir = dirs
    cfg = load_config(config_file)
    rows = build_dashboard(cfg, state_dir, history_dir)
    assert len(rows) == 2
    assert all(r.last_seen == "never" for r in rows)
    assert all(r.status == "MISSING" for r in rows)
    assert all(r.consecutive_failures == 0 for r in rows)


def test_build_dashboard_healthy_job(config_file, dirs):
    state_dir, history_dir = dirs
    cfg = load_config(config_file)
    record_success(state_dir, "backup")
    h = JobHistory(history_dir, "backup")
    h.add(success=True)
    rows = build_dashboard(cfg, state_dir, history_dir)
    backup_row = next(r for r in rows if r.name == "backup")
    assert backup_row.status == "OK"
    assert backup_row.success_rate == 1.0
    assert backup_row.consecutive_failures == 0


def test_build_dashboard_failing_job(config_file, dirs):
    state_dir, history_dir = dirs
    cfg = load_config(config_file)
    record_failure(state_dir, "cleanup")
    h = JobHistory(history_dir, "cleanup")
    h.add(success=False)
    h.add(success=False)
    rows = build_dashboard(cfg, state_dir, history_dir)
    cleanup_row = next(r for r in rows if r.name == "cleanup")
    assert cleanup_row.status == "FAILING"
    assert cleanup_row.consecutive_failures == 2


def test_render_text_empty():
    output = render_text([])
    assert "No jobs" in output


def test_render_text_contains_job_names(config_file, dirs):
    state_dir, history_dir = dirs
    cfg = load_config(config_file)
    rows = build_dashboard(cfg, state_dir, history_dir)
    output = render_text(rows)
    assert "backup" in output
    assert "cleanup" in output
    assert "STATUS" in output
    assert "MISSING" in output


def test_cmd_dashboard_returns_0_when_all_ok(config_file, dirs, monkeypatch):
    import argparse
    from cronwatch.cli_dashboard import cmd_dashboard

    state_dir, history_dir = dirs
    cfg = load_config(config_file)
    for job in cfg.jobs:
        record_success(state_dir, job.name)
        h = JobHistory(history_dir, job.name)
        h.add(success=True)

    args = argparse.Namespace(
        config=config_file,
        state_dir=state_dir,
        history_dir=history_dir,
        format="text",
    )
    assert cmd_dashboard(args) == 0


def test_cmd_dashboard_returns_1_when_failing(config_file, dirs):
    import argparse
    from cronwatch.cli_dashboard import cmd_dashboard

    state_dir, history_dir = dirs
    args = argparse.Namespace(
        config=config_file,
        state_dir=state_dir,
        history_dir=history_dir,
        format="text",
    )
    assert cmd_dashboard(args) == 1


def test_cmd_dashboard_bad_config(tmp_path, dirs):
    import argparse
    from cronwatch.cli_dashboard import cmd_dashboard

    state_dir, history_dir = dirs
    args = argparse.Namespace(
        config=str(tmp_path / "missing.json"),
        state_dir=state_dir,
        history_dir=history_dir,
        format="text",
    )
    assert cmd_dashboard(args) == 2
