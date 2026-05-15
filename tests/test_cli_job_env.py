"""Tests for cronwatch.cli_job_env."""
from __future__ import annotations

import pytest

from cronwatch.cli_job_env import cmd_set, cmd_unset, cmd_list, cmd_clear
from cronwatch.job_env import get_env, set_var


@pytest.fixture
def state_dir(tmp_path):
    return str(tmp_path)


class _Args:
    def __init__(self, **kwargs):
        self.__dict__.update(kwargs)


def test_cmd_set_stores_variable(state_dir, capsys):
    args = _Args(state_dir=state_dir, job="backup", key="HOST", value="db1")
    rc = cmd_set(args)
    assert rc == 0
    assert get_env(state_dir, "backup")["HOST"] == "db1"
    out = capsys.readouterr().out
    assert "HOST" in out
    assert "db1" in out


def test_cmd_unset_removes_variable(state_dir, capsys):
    set_var(state_dir, "backup", "HOST", "db1")
    args = _Args(state_dir=state_dir, job="backup", key="HOST")
    rc = cmd_unset(args)
    assert rc == 0
    assert "HOST" not in get_env(state_dir, "backup")


def test_cmd_unset_missing_returns_1(state_dir, capsys):
    args = _Args(state_dir=state_dir, job="backup", key="NOPE")
    rc = cmd_unset(args)
    assert rc == 1


def test_cmd_list_shows_vars(state_dir, capsys):
    set_var(state_dir, "backup", "A", "1")
    set_var(state_dir, "backup", "B", "2")
    args = _Args(state_dir=state_dir, job="backup")
    rc = cmd_list(args)
    assert rc == 0
    out = capsys.readouterr().out
    assert "A=1" in out
    assert "B=2" in out


def test_cmd_list_no_vars(state_dir, capsys):
    args = _Args(state_dir=state_dir, job="backup")
    rc = cmd_list(args)
    assert rc == 0
    out = capsys.readouterr().out
    assert "No environment" in out


def test_cmd_clear_removes_all(state_dir, capsys):
    set_var(state_dir, "backup", "X", "1")
    set_var(state_dir, "backup", "Y", "2")
    args = _Args(state_dir=state_dir, job="backup")
    rc = cmd_clear(args)
    assert rc == 0
    assert get_env(state_dir, "backup") == {}
    out = capsys.readouterr().out
    assert "2" in out
