"""Tests for cronwatch.job_env."""
from __future__ import annotations

import pytest

from cronwatch.job_env import (
    set_var,
    unset_var,
    get_env,
    clear_env,
    build_env,
    _env_path,
)


@pytest.fixture
def state_dir(tmp_path):
    return str(tmp_path)


def test_get_env_empty_when_no_file(state_dir):
    assert get_env(state_dir, "backup") == {}


def test_set_var_creates_entry(state_dir):
    set_var(state_dir, "backup", "DB_HOST", "localhost")
    env = get_env(state_dir, "backup")
    assert env["DB_HOST"] == "localhost"


def test_set_var_multiple_keys(state_dir):
    set_var(state_dir, "backup", "A", "1")
    set_var(state_dir, "backup", "B", "2")
    env = get_env(state_dir, "backup")
    assert env == {"A": "1", "B": "2"}


def test_set_var_overwrites_existing(state_dir):
    set_var(state_dir, "backup", "KEY", "old")
    set_var(state_dir, "backup", "KEY", "new")
    assert get_env(state_dir, "backup")["KEY"] == "new"


def test_unset_var_returns_true_when_exists(state_dir):
    set_var(state_dir, "backup", "KEY", "val")
    result = unset_var(state_dir, "backup", "KEY")
    assert result is True
    assert "KEY" not in get_env(state_dir, "backup")


def test_unset_var_returns_false_when_missing(state_dir):
    result = unset_var(state_dir, "backup", "NOPE")
    assert result is False


def test_clear_env_removes_all(state_dir):
    set_var(state_dir, "backup", "A", "1")
    set_var(state_dir, "backup", "B", "2")
    count = clear_env(state_dir, "backup")
    assert count == 2
    assert get_env(state_dir, "backup") == {}


def test_clear_env_no_file_returns_zero(state_dir):
    count = clear_env(state_dir, "nonexistent")
    assert count == 0


def test_jobs_are_isolated(state_dir):
    set_var(state_dir, "job_a", "KEY", "for_a")
    set_var(state_dir, "job_b", "KEY", "for_b")
    assert get_env(state_dir, "job_a")["KEY"] == "for_a"
    assert get_env(state_dir, "job_b")["KEY"] == "for_b"


def test_build_env_includes_os_env(state_dir, monkeypatch):
    monkeypatch.setenv("EXISTING_VAR", "from_os")
    env = build_env(state_dir, "backup")
    assert env["EXISTING_VAR"] == "from_os"


def test_build_env_overrides_os_env(state_dir, monkeypatch):
    monkeypatch.setenv("MY_VAR", "os_value")
    set_var(state_dir, "backup", "MY_VAR", "override")
    env = build_env(state_dir, "backup")
    assert env["MY_VAR"] == "override"


def test_env_path_sanitizes_slashes(state_dir):
    path = _env_path(state_dir, "my/job/name")
    assert "/" not in path.name
