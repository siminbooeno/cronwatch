"""Tests for cronwatch.cli."""

import json
import pytest
from unittest.mock import patch, MagicMock

from cronwatch.cli import cmd_run, cmd_check, _build_parser


@pytest.fixture
def config_file(tmp_path):
    cfg = {
        "jobs": [
            {"name": "ok_job", "schedule": "* * * * *", "command": "echo hi", "grace_minutes": 5}
        ],
        "alert": {"webhook_url": "http://example.com/hook"}
    }
    p = tmp_path / "cronwatch.json"
    p.write_text(json.dumps(cfg))
    return str(p)


@pytest.fixture
def state_dir(tmp_path):
    d = tmp_path / "state"
    d.mkdir()
    return str(d)


def test_cmd_run_success(config_file, state_dir):
    with patch("cronwatch.cli.run_job", return_value=True) as mock_run:
        code = cmd_run(config_file, state_dir)
    assert code == 0
    mock_run.assert_called_once()


def test_cmd_run_failure_returns_1(config_file, state_dir):
    with patch("cronwatch.cli.run_job", return_value=False):
        with patch("cronwatch.cli.dispatch_alert") as mock_alert:
            code = cmd_run(config_file, state_dir)
    assert code == 1
    mock_alert.assert_called_once()


def test_cmd_check_no_overdue(config_file, state_dir):
    with patch("cronwatch.cli.check_jobs", return_value=[]) as mock_check:
        code = cmd_check(config_file, state_dir)
    assert code == 0


def test_cmd_check_overdue_dispatches_alert(config_file, state_dir):
    with patch("cronwatch.cli.check_jobs", return_value=["ok_job"]):
        with patch("cronwatch.cli.dispatch_alert") as mock_alert:
            code = cmd_check(config_file, state_dir)
    assert code == 1
    mock_alert.assert_called_once()


def test_parser_requires_config():
    parser = _build_parser()
    with pytest.raises(SystemExit):
        parser.parse_args(["run"])


def test_parser_run_subcommand():
    parser = _build_parser()
    args = parser.parse_args(["-c", "cfg.json", "run"])
    assert args.command == "run"
    assert args.config == "cfg.json"


def test_parser_check_subcommand():
    parser = _build_parser()
    args = parser.parse_args(["-c", "cfg.json", "--state-dir", "/tmp/s", "check"])
    assert args.command == "check"
    assert args.state_dir == "/tmp/s"
