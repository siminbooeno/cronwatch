"""Tests for cronwatch.cli_job_trends."""
from __future__ import annotations

import json
from pathlib import Path

import pytest

from cronwatch.history import JobHistory
from cronwatch.cli_job_trends import cmd_list, cmd_show, _build_parser


@pytest.fixture()
def dirs(tmp_path: Path):
    cfg_dir = tmp_path / "cfg"
    cfg_dir.mkdir()
    hist_dir = tmp_path / "history"
    hist_dir.mkdir()
    return cfg_dir, hist_dir


def _write_config(cfg_dir: Path, job_names) -> Path:
    import json as _json
    cfg = {
        "jobs": [{"name": n, "command": f"echo {n}", "interval_minutes": 60} for n in job_names],
        "alerts": {"webhook_url": None},
    }
    p = cfg_dir / "config.json"
    p.write_text(_json.dumps(cfg))
    return p


def _add(hist_dir: Path, job: str, duration: float):
    jh = JobHistory(job, hist_dir)
    jh.add(success=True, duration_seconds=duration, exit_code=0, output="")


class _Args:
    def __init__(self, **kw):
        self.__dict__.update(kw)


def test_cmd_list_no_history(dirs):
    cfg_dir, hist_dir = dirs
    cfg_path = _write_config(cfg_dir, ["job1"])
    args = _Args(config=str(cfg_path), history_dir=str(hist_dir), as_json=False, limit=50)
    rc = cmd_list(args)
    assert rc == 0


def test_cmd_list_json_output(dirs, capsys):
    cfg_dir, hist_dir = dirs
    cfg_path = _write_config(cfg_dir, ["job1", "job2"])
    _add(hist_dir, "job1", 1.5)
    _add(hist_dir, "job2", 2.5)
    args = _Args(config=str(cfg_path), history_dir=str(hist_dir), as_json=True, limit=50)
    rc = cmd_list(args)
    assert rc == 0
    out = capsys.readouterr().out
    data = json.loads(out)
    assert isinstance(data, list)
    assert len(data) == 2
    names = {d["job"] for d in data}
    assert names == {"job1", "job2"}


def test_cmd_list_text_output(dirs, capsys):
    cfg_dir, hist_dir = dirs
    cfg_path = _write_config(cfg_dir, ["myjob"])
    _add(hist_dir, "myjob", 3.0)
    args = _Args(config=str(cfg_path), history_dir=str(hist_dir), as_json=False, limit=50)
    cmd_list(args)
    out = capsys.readouterr().out
    assert "myjob" in out


def test_cmd_show_json(dirs, capsys):
    cfg_dir, hist_dir = dirs
    _add(hist_dir, "solo", 4.0)
    args = _Args(config=None, history_dir=str(hist_dir), job="solo", as_json=True, limit=50)
    rc = cmd_show(args)
    assert rc == 0
    data = json.loads(capsys.readouterr().out)
    assert data["job"] == "solo"
    assert data["mean_s"] == pytest.approx(4.0)


def test_cmd_show_text(dirs, capsys):
    cfg_dir, hist_dir = dirs
    _add(hist_dir, "solo2", 7.0)
    args = _Args(config=None, history_dir=str(hist_dir), job="solo2", as_json=False, limit=50)
    cmd_show(args)
    out = capsys.readouterr().out
    assert "solo2" in out


def test_parser_subcommands():
    p = _build_parser()
    args = p.parse_args(["--config", "c.json", "--history-dir", "/h", "list"])
    assert args.command == "list"
    args2 = p.parse_args(["--config", "c.json", "--history-dir", "/h", "show", "myjob"])
    assert args2.command == "show"
    assert args2.job == "myjob"
