"""Tests for cronwatch.cli_pauses."""

from __future__ import annotations

from datetime import datetime, timezone, timedelta
from pathlib import Path
from unittest.mock import patch

import pytest

from cronwatch.cli_pauses import cmd_pause, cmd_resume, cmd_status, cmd_list, _build_parser
from cronwatch.pauses import pause_job

FAKE_NOW = datetime(2024, 6, 1, 12, 0, 0, tzinfo=timezone.utc)


@pytest.fixture()
def state_dir(tmp_path: Path) -> str:
    return str(tmp_path)


def _args(state_dir: str, **kwargs):
    import argparse
    ns = argparse.Namespace(state_dir=state_dir, **kwargs)
    return ns


def test_cmd_pause_indefinite(state_dir, capsys):
    args = _args(state_dir, job="backup", reason="", minutes=None, hours=None)
    rc = cmd_pause(args)
    assert rc == 0
    out = capsys.readouterr().out
    assert "backup" in out
    assert "indefinitely" in out


def test_cmd_pause_with_minutes(state_dir, capsys):
    with patch("cronwatch.cli_pauses.datetime") as mock_dt:
        mock_dt.now.return_value = FAKE_NOW
        mock_dt.side_effect = lambda *a, **kw: datetime(*a, **kw)
        args = _args(state_dir, job="backup", reason="deploy", minutes=30, hours=None)
        # Use real datetime for timedelta arithmetic
        with patch("cronwatch.pauses._utcnow", return_value=FAKE_NOW):
            rc = cmd_pause(args)
    assert rc == 0


def test_cmd_resume_existing(state_dir, capsys):
    pause_job(state_dir, "backup")
    args = _args(state_dir, job="backup")
    rc = cmd_resume(args)
    assert rc == 0
    assert "Resumed" in capsys.readouterr().out


def test_cmd_resume_not_paused(state_dir, capsys):
    args = _args(state_dir, job="backup")
    rc = cmd_resume(args)
    assert rc == 1
    assert "not paused" in capsys.readouterr().out


def test_cmd_status_paused(state_dir, capsys):
    pause_job(state_dir, "backup")
    args = _args(state_dir, job="backup")
    rc = cmd_status(args)
    assert rc == 0
    assert "PAUSED" in capsys.readouterr().out


def test_cmd_status_active(state_dir, capsys):
    args = _args(state_dir, job="backup")
    rc = cmd_status(args)
    assert rc == 0
    assert "active" in capsys.readouterr().out


def test_cmd_list_empty(state_dir, capsys):
    args = _args(state_dir)
    rc = cmd_list(args)
    assert rc == 0
    assert "No jobs" in capsys.readouterr().out


def test_cmd_list_shows_paused_jobs(state_dir, capsys):
    pause_job(state_dir, "alpha", reason="testing")
    pause_job(state_dir, "beta")
    args = _args(state_dir)
    rc = cmd_list(args)
    assert rc == 0
    out = capsys.readouterr().out
    assert "alpha" in out
    assert "beta" in out
    assert "testing" in out


def test_parser_pause_command():
    parser = _build_parser()
    args = parser.parse_args(["--state-dir", "/tmp", "pause", "myjob", "--reason", "test"])
    assert args.command == "pause"
    assert args.job == "myjob"
    assert args.reason == "test"


def test_parser_resume_command():
    parser = _build_parser()
    args = parser.parse_args(["resume", "myjob"])
    assert args.command == "resume"
    assert args.job == "myjob"
