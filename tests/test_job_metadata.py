"""Tests for cronwatch.job_metadata."""

import pytest

from cronwatch.job_metadata import (
    set_metadata,
    unset_metadata,
    get_metadata,
    get_value,
    clear_metadata,
)


@pytest.fixture()
def state_dir(tmp_path):
    return str(tmp_path)


def test_get_metadata_empty_when_no_file(state_dir):
    result = get_metadata(state_dir, "backup")
    assert result == {}


def test_get_value_missing_returns_none(state_dir):
    assert get_value(state_dir, "backup", "team") is None


def test_set_metadata_returns_updated_dict(state_dir):
    result = set_metadata(state_dir, "backup", "team", "ops")
    assert result == {"team": "ops"}


def test_set_metadata_persisted(state_dir):
    set_metadata(state_dir, "backup", "team", "ops")
    assert get_value(state_dir, "backup", "team") == "ops"


def test_set_metadata_multiple_keys(state_dir):
    set_metadata(state_dir, "backup", "team", "ops")
    set_metadata(state_dir, "backup", "env", "prod")
    data = get_metadata(state_dir, "backup")
    assert data["team"] == "ops"
    assert data["env"] == "prod"


def test_set_metadata_overwrites_existing(state_dir):
    set_metadata(state_dir, "backup", "team", "ops")
    set_metadata(state_dir, "backup", "team", "platform")
    assert get_value(state_dir, "backup", "team") == "platform"


def test_unset_metadata_removes_key(state_dir):
    set_metadata(state_dir, "backup", "team", "ops")
    removed = unset_metadata(state_dir, "backup", "team")
    assert removed is True
    assert get_value(state_dir, "backup", "team") is None


def test_unset_metadata_returns_false_for_missing_key(state_dir):
    result = unset_metadata(state_dir, "backup", "nonexistent")
    assert result is False


def test_unset_preserves_other_keys(state_dir):
    set_metadata(state_dir, "backup", "team", "ops")
    set_metadata(state_dir, "backup", "env", "prod")
    unset_metadata(state_dir, "backup", "team")
    assert get_value(state_dir, "backup", "env") == "prod"


def test_clear_metadata_returns_count(state_dir):
    set_metadata(state_dir, "backup", "team", "ops")
    set_metadata(state_dir, "backup", "env", "prod")
    count = clear_metadata(state_dir, "backup")
    assert count == 2


def test_clear_metadata_removes_all(state_dir):
    set_metadata(state_dir, "backup", "team", "ops")
    clear_metadata(state_dir, "backup")
    assert get_metadata(state_dir, "backup") == {}


def test_clear_metadata_empty_returns_zero(state_dir):
    assert clear_metadata(state_dir, "backup") == 0


def test_jobs_are_isolated(state_dir):
    set_metadata(state_dir, "job_a", "key", "alpha")
    set_metadata(state_dir, "job_b", "key", "beta")
    assert get_value(state_dir, "job_a", "key") == "alpha"
    assert get_value(state_dir, "job_b", "key") == "beta"
