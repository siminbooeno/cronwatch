"""Tests for cronwatch.cli_job_priority."""
from __future__ import annotations

import json
import pathlib
import pytest

from cronwatch.cli_job_priority import cmd_list, cmd_show


# ---------------------------------------------------------------------------
# fixtures
# ---------------------------------------------------------------------------

@pytest.fixture()
def config_file(tmp_path: pathlib.Path) -> pathlib.Path:
    cfg = {
        "jobs": [
            {
                "name": "alpha",
                "command": "echo alpha",
                "interval_seconds": 60,
                "priority": {"level": "critical", "min_failures_before_alert": 1},
            },
            {
                "name": "beta",
                "command": "echo beta",
                "interval_seconds": 300,
                "priority": {"level": "low", "alert_on_miss": False, "min_failures_before_alert": 5},
            },
        ],
        "alerts": {"webhook_url": "http://example.com/hook"},
    }
    p = tmp_path / "config.json"
    p.write_text(json.dumps(cfg))
    return p


class _Args:
    def __init__(self, **kw):
        for k, v in kw.items():
            setattr(self, k, v)


# ---------------------------------------------------------------------------
# cmd_list
# ---------------------------------------------------------------------------

def test_cmd_list_returns_zero(config_file, capsys):
    rc = cmd_list(_Args(config=str(config_file)))
    assert rc == 0


def test_cmd_list_shows_jobs(config_file, capsys):
    cmd_list(_Args(config=str(config_file)))
    out = capsys.readouterr().out
    assert "alpha" in out
    assert "beta" in out
    # critical sorts before low
    assert out.index("alpha") < out.index("beta")


def test_cmd_list_shows_priority_level(config_file, capsys):
    cmd_list(_Args(config=str(config_file)))
    out = capsys.readouterr().out
    assert "critical" in out
    assert "low" in out


# ---------------------------------------------------------------------------
# cmd_show
# ---------------------------------------------------------------------------

def test_cmd_show_existing_job(config_file, capsys):
    rc = cmd_show(_Args(config=str(config_file), job="beta"))
    assert rc == 0
    out = capsys.readouterr().out
    assert "low" in out
    assert "False" in out  # alert_on_miss
    assert "5" in out       # min_failures_before_alert


def test_cmd_show_missing_job_returns_1(config_file, capsys):
    rc = cmd_show(_Args(config=str(config_file), job="nonexistent"))
    assert rc == 1
