"""Tests for cronwatch.cli_retention_policy."""
from __future__ import annotations

import json
import pytest
from unittest.mock import patch, MagicMock

from cronwatch.cli_retention_policy import cmd_show, _build_parser
from cronwatch.retention_policy import RetentionPolicy


def _make_job(name, retention=None):
    j = MagicMock()
    j.name = name
    j.retention = retention
    return j


def _make_cfg(*job_names, global_retention=None):
    cfg = MagicMock()
    cfg.jobs = [_make_job(n) for n in job_names]
    cfg.retention = global_retention
    return cfg


class _Args:
    def __init__(self, config="cfg.json", job=None, as_json=False):
        self.config = config
        self.job = job
        self.as_json = as_json


def test_cmd_show_all_jobs(capsys):
    cfg = _make_cfg("alpha", "beta")
    with patch("cronwatch.cli_retention_policy.load_config", return_value=cfg):
        rc = cmd_show(_Args())
    assert rc == 0
    out = capsys.readouterr().out
    assert "alpha" in out
    assert "beta" in out


def test_cmd_show_single_job(capsys):
    cfg = _make_cfg("alpha", "beta")
    with patch("cronwatch.cli_retention_policy.load_config", return_value=cfg):
        rc = cmd_show(_Args(job="alpha"))
    assert rc == 0
    out = capsys.readouterr().out
    assert "alpha" in out
    assert "beta" not in out


def test_cmd_show_json_output(capsys):
    cfg = _make_cfg("myjob")
    with patch("cronwatch.cli_retention_policy.load_config", return_value=cfg):
        rc = cmd_show(_Args(as_json=True))
    assert rc == 0
    data = json.loads(capsys.readouterr().out)
    assert isinstance(data, list)
    assert data[0]["job"] == "myjob"
    assert "history_days" in data[0]
    assert "state_days" in data[0]


def test_cmd_show_json_max_records_none(capsys):
    cfg = _make_cfg("j1")
    with patch("cronwatch.cli_retention_policy.load_config", return_value=cfg):
        cmd_show(_Args(as_json=True))
    data = json.loads(capsys.readouterr().out)
    assert data[0]["max_records"] is None


def test_cmd_show_text_unlimited_label(capsys):
    cfg = _make_cfg("j1")
    with patch("cronwatch.cli_retention_policy.load_config", return_value=cfg):
        cmd_show(_Args())
    out = capsys.readouterr().out
    assert "unlimited" in out


def test_parser_show_subcommand():
    parser = _build_parser()
    args = parser.parse_args(["--config", "c.json", "show", "--json"])
    assert args.command == "show"
    assert args.as_json is True
    assert args.config == "c.json"
