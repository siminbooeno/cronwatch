"""Tests for cronwatch.cli_watch_history."""
from __future__ import annotations

import io
import json
from pathlib import Path

import pytest

from cronwatch.history import JobHistory
from cronwatch.cli_watch_history import _build_parser, cmd_show


@pytest.fixture()
def history_dir(tmp_path: Path) -> Path:
    d = tmp_path / "history"
    d.mkdir()
    return d


def _args(job: str, history_dir: Path, limit: int = 20, failures_only: bool = False, as_json: bool = False):
    class A:
        pass

    a = A()
    a.job = job
    a.history_dir = str(history_dir)
    a.limit = limit
    a.failures_only = failures_only
    a.as_json = as_json
    return a


def _add(jh: JobHistory, success: bool, exit_code: int = 0, duration: float = 1.0) -> None:
    from cronwatch.history import add
    add(jh, success=success, exit_code=exit_code, duration_s=duration)


def test_no_history_prints_message(history_dir: Path) -> None:
    out = io.StringIO()
    rc = cmd_show(_args("myjob", history_dir), out=out)
    assert rc == 0
    assert "No history" in out.getvalue()


def test_shows_records_in_table(history_dir: Path) -> None:
    jh = JobHistory(job_name="myjob", history_dir=history_dir)
    _add(jh, success=True, exit_code=0, duration=2.5)
    _add(jh, success=False, exit_code=1, duration=0.1)

    out = io.StringIO()
    rc = cmd_show(_args("myjob", history_dir), out=out)
    assert rc == 0
    text = out.getvalue()
    assert "OK" in text
    assert "FAIL" in text
    assert "50.0%" in text


def test_failures_only_filter(history_dir: Path) -> None:
    jh = JobHistory(job_name="myjob", history_dir=history_dir)
    _add(jh, success=True)
    _add(jh, success=False, exit_code=2)

    out = io.StringIO()
    cmd_show(_args("myjob", history_dir, failures_only=True), out=out)
    text = out.getvalue()
    assert "FAIL" in text
    assert "OK" not in text.split("\n")[2]  # header row excluded


def test_limit_restricts_output(history_dir: Path) -> None:
    jh = JobHistory(job_name="myjob", history_dir=history_dir)
    for _ in range(10):
        _add(jh, success=True)

    out = io.StringIO()
    cmd_show(_args("myjob", history_dir, limit=3), out=out)
    lines = [l for l in out.getvalue().splitlines() if "OK" in l or "FAIL" in l]
    assert len(lines) == 3


def test_json_output(history_dir: Path) -> None:
    jh = JobHistory(job_name="myjob", history_dir=history_dir)
    _add(jh, success=True, exit_code=0, duration=1.23)

    out = io.StringIO()
    cmd_show(_args("myjob", history_dir, as_json=True), out=out)
    line = out.getvalue().strip().splitlines()[0]
    data = json.loads(line)
    assert data["success"] is True
    assert data["exit_code"] == 0
    assert abs(data["duration_s"] - 1.23) < 0.01


def test_build_parser_defaults() -> None:
    p = _build_parser()
    args = p.parse_args(["somejob"])
    assert args.job == "somejob"
    assert args.limit == 20
    assert args.failures_only is False
    assert args.as_json is False
