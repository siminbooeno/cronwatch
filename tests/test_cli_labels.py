"""Tests for cronwatch.cli_labels."""
import json
import os
import pytest

from cronwatch.cli_labels import cmd_select, cmd_keys, cmd_values


@pytest.fixture
def config_file(tmp_path):
    cfg = {
        "state_dir": str(tmp_path / "state"),
        "history_dir": str(tmp_path / "history"),
        "alert": {},
        "jobs": [
            {
                "name": "backup",
                "command": "echo backup",
                "interval_seconds": 3600,
                "labels": {"env": "prod", "team": "infra"},
            },
            {
                "name": "report",
                "command": "echo report",
                "interval_seconds": 86400,
                "labels": {"env": "prod", "team": "analytics"},
            },
            {
                "name": "cleanup",
                "command": "echo cleanup",
                "interval_seconds": 3600,
                "labels": {"env": "staging", "team": "infra"},
            },
        ],
    }
    p = tmp_path / "config.json"
    p.write_text(json.dumps(cfg))
    return str(p)


@pytest.fixture
def config_file_no_labels(tmp_path):
    """Config file where jobs have no labels defined."""
    cfg = {
        "state_dir": str(tmp_path / "state"),
        "history_dir": str(tmp_path / "history"),
        "alert": {},
        "jobs": [
            {
                "name": "nolabeljob",
                "command": "echo nolabel",
                "interval_seconds": 3600,
            },
        ],
    }
    p = tmp_path / "config.json"
    p.write_text(json.dumps(cfg))
    return str(p)


class _Args:
    def __init__(self, **kw):
        self.__dict__.update(kw)


def test_cmd_select_matching(config_file, capsys):
    args = _Args(config=config_file, selector="env=prod")
    rc = cmd_select(args)
    assert rc == 0
    out = capsys.readouterr().out
    assert "backup" in out
    assert "report" in out
    assert "cleanup" not in out


def test_cmd_select_no_match(config_file, capsys):
    args = _Args(config=config_file, selector="env=dev")
    rc = cmd_select(args)
    assert rc == 0
    assert "No jobs" in capsys.readouterr().out


def test_cmd_select_invalid_selector(config_file, capsys):
    args = _Args(config=config_file, selector="badvalue")
    rc = cmd_select(args)
    assert rc == 1
    assert "Error" in capsys.readouterr().err


def test_cmd_keys(config_file, capsys):
    args = _Args(config=config_file)
    rc = cmd_keys(args)
    assert rc == 0
    out = capsys.readouterr().out
    assert "env" in out
    assert "team" in out


def test_cmd_keys_no_labels(config_file_no_labels, capsys):
    """cmd_keys should handle jobs with no labels without crashing."""
    args = _Args(config=config_file_no_labels)
    rc = cmd_keys(args)
    assert rc == 0


def test_cmd_values_known_key(config_file, capsys):
    args = _Args(config=config_file, key="env")
    rc = cmd_values(args)
    assert rc == 0
    out = capsys.readouterr().out
    assert "prod" in out
    assert "staging" in out


def test_cmd_values_unknown_key(config_file, capsys):
    args = _Args(config=config_file, key="owner")
    rc = cmd_values(args)
    assert rc == 0
    assert "No values" in capsys.readouterr().out
