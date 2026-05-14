"""Tests for cronwatch.cli_sla."""
from __future__ import annotations

import json
import os
import pytest

from cronwatch.cli_sla import cmd_check, _build_parser
from cronwatch.history import JobHistory


@pytest.fixture()
def dirs(tmp_path):
    cfg_dir = tmp_path / "cfg"
    cfg_dir.mkdir()
    hist_dir = tmp_path / "history"
    hist_dir.mkdir()
    return cfg_dir, hist_dir


def _write_config(cfg_dir, jobs_extra: str = "") -> str:
    path = str(cfg_dir / "cronwatch.json")
    with open(path, "w") as fh:
        fh.write(
            json.dumps(
                {
                    "jobs": [
                        {
                            "name": "backup",
                            "command": "echo backup",
                            "interval": 3600,
                            "sla": {"min_success_rate": 0.8, "window": 5},
                        },
                        {
                            "name": "report",
                            "command": "echo report",
                            "interval": 7200,
                        },
                    ],
                    "alerts": {"webhook_url": ""},
                }
            )
        )
    return path


def _add_records(hist_dir, job_name, outcomes):
    hist = JobHistory(job_name, str(hist_dir))
    for o in outcomes:
        hist.add(success=(o == "success"), duration=1.0)


class _Args:
    def __init__(self, config, history_dir, job=None, as_json=False):
        self.config = config
        self.history_dir = history_dir
        self.job = job
        self.as_json = as_json


def test_cmd_check_all_satisfied(dirs, capsys):
    cfg_dir, hist_dir = dirs
    cfg = _write_config(cfg_dir)
    _add_records(hist_dir, "backup", ["success"] * 5)
    rc = cmd_check(_Args(cfg, str(hist_dir)))
    assert rc == 0
    out = capsys.readouterr().out
    assert "All SLAs satisfied" in out


def test_cmd_check_violation_exits_1(dirs, capsys):
    cfg_dir, hist_dir = dirs
    cfg = _write_config(cfg_dir)
    _add_records(hist_dir, "backup", ["failure"] * 5)
    rc = cmd_check(_Args(cfg, str(hist_dir)))
    assert rc == 1
    out = capsys.readouterr().out
    assert "VIOLATION" in out
    assert "backup" in out


def test_cmd_check_single_job(dirs, capsys):
    cfg_dir, hist_dir = dirs
    cfg = _write_config(cfg_dir)
    _add_records(hist_dir, "backup", ["success"] * 5)
    rc = cmd_check(_Args(cfg, str(hist_dir), job="backup"))
    assert rc == 0


def test_cmd_check_unknown_job_returns_2(dirs, capsys):
    cfg_dir, hist_dir = dirs
    cfg = _write_config(cfg_dir)
    rc = cmd_check(_Args(cfg, str(hist_dir), job="nonexistent"))
    assert rc == 2


def test_cmd_check_json_output(dirs, capsys):
    cfg_dir, hist_dir = dirs
    cfg = _write_config(cfg_dir)
    _add_records(hist_dir, "backup", ["failure"] * 5)
    rc = cmd_check(_Args(cfg, str(hist_dir), as_json=True))
    assert rc == 1
    data = json.loads(capsys.readouterr().out)
    assert isinstance(data, list)
    assert data[0]["job"] == "backup"
    assert "reason" in data[0]
