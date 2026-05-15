"""Tests for cronwatch.cli_thresholds."""
from __future__ import annotations

import json
import os
import pytest

from cronwatch.cli_thresholds import cmd_check, _build_parser
from cronwatch.history import JobHistory


@pytest.fixture()
def dirs(tmp_path):
    cfg_dir = tmp_path / "cfg"
    cfg_dir.mkdir()
    hist_dir = tmp_path / "history"
    hist_dir.mkdir()
    return str(cfg_dir), str(hist_dir)


def _write_config(cfg_dir: str, job_names: list[str]) -> str:
    path = os.path.join(cfg_dir, "cronwatch.json")
    data = {
        "jobs": [{"name": n, "command": "echo hi", "interval_seconds": 3600} for n in job_names],
        "alert": {},
    }
    with open(path, "w") as f:
        json.dump(data, f)
    return path


def _add_records(history_dir: str, job_name: str, outcomes: list[bool]) -> None:
    hist = JobHistory(history_dir, job_name)
    for s in outcomes:
        hist.add(success=s, duration=1.0)


class _Args:
    def __init__(self, config, history_dir, window=20, level=None, exit_code=False):
        self.config = config
        self.history_dir = history_dir
        self.window = window
        self.level = level
        self.exit_code = exit_code


def test_cmd_check_no_violations(dirs, capsys):
    cfg_dir, hist_dir = dirs
    cfg = _write_config(cfg_dir, ["clean_job"])
    _add_records(hist_dir, "clean_job", [True] * 10)
    rc = cmd_check(_Args(cfg, hist_dir))
    assert rc == 0
    out = capsys.readouterr().out
    assert "No threshold violations" in out


def test_cmd_check_with_violation(dirs, capsys):
    cfg_dir, hist_dir = dirs
    cfg = _write_config(cfg_dir, ["bad_job"])
    _add_records(hist_dir, "bad_job", [False] * 10)
    rc = cmd_check(_Args(cfg, hist_dir))
    assert rc == 0  # exit_code flag not set
    out = capsys.readouterr().out
    assert "bad_job" in out


def test_cmd_check_exit_code_on_violation(dirs):
    cfg_dir, hist_dir = dirs
    cfg = _write_config(cfg_dir, ["bad_job"])
    _add_records(hist_dir, "bad_job", [False] * 10)
    rc = cmd_check(_Args(cfg, hist_dir, exit_code=True))
    assert rc == 1


def test_cmd_check_level_filter(dirs, capsys):
    cfg_dir, hist_dir = dirs
    cfg = _write_config(cfg_dir, ["warn_job"])
    # 2 consecutive failures -> warn but not crit
    _add_records(hist_dir, "warn_job", [True] * 8 + [False, False])
    rc = cmd_check(_Args(cfg, hist_dir, level="crit"))
    assert rc == 0
    out = capsys.readouterr().out
    assert "No threshold violations" in out


def test_build_parser_defaults():
    p = _build_parser()
    args = p.parse_args(["--config", "c.json", "--history-dir", "/tmp/h"])
    assert args.window == 20
    assert args.level is None
    assert args.exit_code is False
