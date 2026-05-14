"""Tests for cronwatch.runbook and cronwatch.cli_runbook."""

from __future__ import annotations

import pytest

from cronwatch.runbook import (
    delete_runbook,
    enrich_alert_message,
    get_runbook,
    list_runbooks,
    set_runbook,
)
from cronwatch.cli_runbook import cmd_delete, cmd_get, cmd_list, cmd_set


@pytest.fixture()
def state_dir(tmp_path):
    return str(tmp_path)


# --- runbook module ---

def test_get_runbook_missing_returns_none(state_dir):
    assert get_runbook(state_dir, "backup") is None


def test_set_and_get_runbook(state_dir):
    set_runbook(state_dir, "backup", "https://wiki.example.com/backup")
    assert get_runbook(state_dir, "backup") == "https://wiki.example.com/backup"


def test_set_overwrites_existing(state_dir):
    set_runbook(state_dir, "backup", "https://old.example.com")
    set_runbook(state_dir, "backup", "https://new.example.com")
    assert get_runbook(state_dir, "backup") == "https://new.example.com"


def test_delete_existing_returns_true(state_dir):
    set_runbook(state_dir, "sync", "https://wiki.example.com/sync")
    assert delete_runbook(state_dir, "sync") is True
    assert get_runbook(state_dir, "sync") is None


def test_delete_missing_returns_false(state_dir):
    assert delete_runbook(state_dir, "nonexistent") is False


def test_list_runbooks_empty(state_dir):
    assert list_runbooks(state_dir) == []


def test_list_runbooks_sorted(state_dir):
    set_runbook(state_dir, "zzz", "https://z.example.com")
    set_runbook(state_dir, "aaa", "https://a.example.com")
    entries = list_runbooks(state_dir)
    assert entries[0]["job"] == "aaa"
    assert entries[1]["job"] == "zzz"


def test_enrich_alert_message_with_runbook(state_dir):
    set_runbook(state_dir, "deploy", "https://wiki.example.com/deploy")
    result = enrich_alert_message(state_dir, "deploy", "Job failed")
    assert "Job failed" in result
    assert "https://wiki.example.com/deploy" in result


def test_enrich_alert_message_without_runbook(state_dir):
    result = enrich_alert_message(state_dir, "deploy", "Job failed")
    assert result == "Job failed"


# --- CLI commands ---

class _Args:
    def __init__(self, **kwargs):
        for k, v in kwargs.items():
            setattr(self, k, v)


def test_cmd_set_returns_0(state_dir, capsys):
    args = _Args(state_dir=state_dir, job="backup", url="https://wiki.example.com")
    assert cmd_set(args) == 0
    out = capsys.readouterr().out
    assert "backup" in out


def test_cmd_get_existing(state_dir, capsys):
    set_runbook(state_dir, "backup", "https://wiki.example.com")
    args = _Args(state_dir=state_dir, job="backup")
    assert cmd_get(args) == 0
    assert "https://wiki.example.com" in capsys.readouterr().out


def test_cmd_get_missing_returns_1(state_dir):
    args = _Args(state_dir=state_dir, job="missing")
    assert cmd_get(args) == 1


def test_cmd_delete_existing_returns_0(state_dir):
    set_runbook(state_dir, "sync", "https://wiki.example.com/sync")
    args = _Args(state_dir=state_dir, job="sync")
    assert cmd_delete(args) == 0


def test_cmd_delete_missing_returns_1(state_dir):
    args = _Args(state_dir=state_dir, job="ghost")
    assert cmd_delete(args) == 1


def test_cmd_list_empty(state_dir, capsys):
    args = _Args(state_dir=state_dir)
    assert cmd_list(args) == 0
    assert "No runbooks" in capsys.readouterr().out


def test_cmd_list_with_entries(state_dir, capsys):
    set_runbook(state_dir, "deploy", "https://wiki.example.com/deploy")
    args = _Args(state_dir=state_dir)
    assert cmd_list(args) == 0
    out = capsys.readouterr().out
    assert "deploy" in out
    assert "https://wiki.example.com/deploy" in out
