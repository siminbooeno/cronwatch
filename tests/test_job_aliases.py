"""Tests for cronwatch.job_aliases and cli_job_aliases."""
from __future__ import annotations

import pytest

from cronwatch.job_aliases import (
    aliases_for_job,
    list_aliases,
    remove_alias,
    resolve_alias,
    set_alias,
)
from cronwatch.cli_job_aliases import (
    cmd_for_job,
    cmd_list,
    cmd_remove,
    cmd_resolve,
    cmd_set,
)


@pytest.fixture()
def state_dir(tmp_path):
    return str(tmp_path)


class _Args:
    def __init__(self, **kwargs):
        self.__dict__.update(kwargs)


def test_resolve_missing_returns_none(state_dir):
    assert resolve_alias(state_dir, "daily") is None


def test_set_and_resolve(state_dir):
    set_alias(state_dir, "daily", "backup-job")
    assert resolve_alias(state_dir, "daily") == "backup-job"


def test_set_overwrites(state_dir):
    set_alias(state_dir, "daily", "old-job")
    set_alias(state_dir, "daily", "new-job")
    assert resolve_alias(state_dir, "daily") == "new-job"


def test_remove_existing_returns_true(state_dir):
    set_alias(state_dir, "daily", "backup-job")
    assert remove_alias(state_dir, "daily") is True
    assert resolve_alias(state_dir, "daily") is None


def test_remove_missing_returns_false(state_dir):
    assert remove_alias(state_dir, "nonexistent") is False


def test_list_aliases_empty(state_dir):
    assert list_aliases(state_dir) == {}


def test_list_aliases_multiple(state_dir):
    set_alias(state_dir, "a", "job-a")
    set_alias(state_dir, "b", "job-b")
    result = list_aliases(state_dir)
    assert result == {"a": "job-a", "b": "job-b"}


def test_aliases_for_job_empty(state_dir):
    assert aliases_for_job(state_dir, "backup-job") == []


def test_aliases_for_job_found(state_dir):
    set_alias(state_dir, "daily", "backup-job")
    set_alias(state_dir, "nightly", "backup-job")
    set_alias(state_dir, "other", "other-job")
    result = aliases_for_job(state_dir, "backup-job")
    assert sorted(result) == ["daily", "nightly"]


def test_cmd_set_returns_zero(state_dir, capsys):
    args = _Args(state_dir=state_dir, alias="x", job_name="my-job")
    assert cmd_set(args) == 0
    assert resolve_alias(state_dir, "x") == "my-job"


def test_cmd_remove_returns_one_when_missing(state_dir):
    args = _Args(state_dir=state_dir, alias="ghost")
    assert cmd_remove(args) == 1


def test_cmd_resolve_prints_target(state_dir, capsys):
    set_alias(state_dir, "q", "target-job")
    args = _Args(state_dir=state_dir, alias="q")
    assert cmd_resolve(args) == 0
    assert capsys.readouterr().out.strip() == "target-job"


def test_cmd_resolve_returns_one_when_missing(state_dir):
    args = _Args(state_dir=state_dir, alias="missing")
    assert cmd_resolve(args) == 1


def test_cmd_list_no_aliases(state_dir, capsys):
    args = _Args(state_dir=state_dir)
    assert cmd_list(args) == 0
    assert "No aliases" in capsys.readouterr().out


def test_cmd_for_job_no_aliases(state_dir, capsys):
    args = _Args(state_dir=state_dir, job_name="unknown")
    assert cmd_for_job(args) == 0
    assert "No aliases" in capsys.readouterr().out
