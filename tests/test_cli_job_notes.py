"""Tests for cronwatch.cli_job_notes CLI commands."""
from __future__ import annotations

import pytest

from cronwatch.job_notes import add_note
from cronwatch.cli_job_notes import cmd_add, cmd_list, cmd_delete, cmd_clear


@pytest.fixture()
def state_dir(tmp_path):
    return str(tmp_path)


class _Args:
    def __init__(self, **kwargs):
        self.__dict__.update(kwargs)


def test_cmd_add_prints_id(state_dir, capsys):
    args = _Args(state_dir=state_dir, job="backup", text="hello", author=None)
    rc = cmd_add(args)
    assert rc == 0
    out = capsys.readouterr().out
    assert "backup" in out
    assert "Added note" in out


def test_cmd_list_no_notes(state_dir, capsys):
    args = _Args(state_dir=state_dir, job="backup")
    rc = cmd_list(args)
    assert rc == 0
    out = capsys.readouterr().out
    assert "No notes" in out


def test_cmd_list_shows_notes(state_dir, capsys):
    add_note(state_dir, "backup", "Important reminder", author="bob")
    args = _Args(state_dir=state_dir, job="backup")
    rc = cmd_list(args)
    assert rc == 0
    out = capsys.readouterr().out
    assert "Important reminder" in out
    assert "bob" in out


def test_cmd_delete_existing(state_dir, capsys):
    rec = add_note(state_dir, "backup", "remove me")
    args = _Args(state_dir=state_dir, job="backup", id=rec["id"])
    rc = cmd_delete(args)
    assert rc == 0
    assert "Deleted" in capsys.readouterr().out


def test_cmd_delete_missing(state_dir, capsys):
    args = _Args(state_dir=state_dir, job="backup", id="no-such-id")
    rc = cmd_delete(args)
    assert rc == 1
    assert "not found" in capsys.readouterr().err


def test_cmd_clear(state_dir, capsys):
    add_note(state_dir, "backup", "a")
    add_note(state_dir, "backup", "b")
    args = _Args(state_dir=state_dir, job="backup")
    rc = cmd_clear(args)
    assert rc == 0
    out = capsys.readouterr().out
    assert "2" in out
