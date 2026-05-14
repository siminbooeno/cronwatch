"""Tests for cronwatch.cli_dependencies."""

from __future__ import annotations

import json
import os
import time
from pathlib import Path

import pytest

from cronwatch.cli_dependencies import cmd_check, cmd_ready


@pytest.fixture()
def config_file(tmp_path: Path) -> str:
    cfg = {
        "jobs": [
            {"name": "setup", "command": "echo setup", "interval_seconds": 3600, "grace_seconds": 60},
            {"name": "backup", "command": "echo backup", "interval_seconds": 3600,
             "grace_seconds": 60, "depends_on": ["setup"]},
        ],
        "alert": {},
        "state_dir": str(tmp_path),
    }
    p = tmp_path / "config.json"
    p.write_text(json.dumps(cfg))
    return str(p)


@pytest.fixture()
def state_dir(tmp_path: Path) -> str:
    return str(tmp_path)


class _Args:
    def __init__(self, **kwargs):
        self.__dict__.update(kwargs)


def _write_success(state_dir: str, job_name: str, ago: float = 0) -> None:
    job_dir = os.path.join(state_dir, job_name)
    os.makedirs(job_dir, exist_ok=True)
    ts = time.time() - ago
    rec = {"timestamp": ts, "success": True, "duration": 1.0, "exit_code": 0}
    with open(os.path.join(job_dir, f"{int(ts)}.json"), "w") as f:
        json.dump(rec, f)


def test_cmd_check_satisfied(config_file, state_dir, capsys):
    _write_success(state_dir, "setup", ago=100)
    args = _Args(config=config_file, state_dir=state_dir, job="backup")
    rc = cmd_check(args)
    assert rc == 0
    assert "OK" in capsys.readouterr().out


def test_cmd_check_blocked(config_file, state_dir, capsys):
    args = _Args(config=config_file, state_dir=state_dir, job="backup")
    rc = cmd_check(args)
    assert rc == 1
    assert "BLOCKED" in capsys.readouterr().out


def test_cmd_check_unknown_job(config_file, state_dir, capsys):
    args = _Args(config=config_file, state_dir=state_dir, job="ghost")
    rc = cmd_check(args)
    assert rc == 2


def test_cmd_ready_lists_unblocked(config_file, state_dir, capsys):
    args = _Args(config=config_file, state_dir=state_dir)
    rc = cmd_ready(args)
    assert rc == 0
    out = capsys.readouterr().out
    assert "setup" in out
    assert "backup" not in out
