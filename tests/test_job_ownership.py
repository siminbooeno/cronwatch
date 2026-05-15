"""Tests for cronwatch.job_ownership."""
import pytest
from cronwatch.job_ownership import (
    set_owner, remove_owner, get_owner, list_owners,
    jobs_owned_by, jobs_owned_by_team,
)


@pytest.fixture
def state_dir(tmp_path):
    return str(tmp_path)


def test_get_owner_missing_returns_none(state_dir):
    assert get_owner(state_dir, "backup") is None


def test_set_owner_returns_record(state_dir):
    rec = set_owner(state_dir, "backup", "alice")
    assert rec["job"] == "backup"
    assert rec["owner"] == "alice"
    assert rec["email"] is None
    assert rec["team"] is None
    assert "assigned_at" in rec


def test_set_owner_with_email_and_team(state_dir):
    rec = set_owner(state_dir, "cleanup", "bob", email="bob@example.com", team="ops")
    assert rec["email"] == "bob@example.com"
    assert rec["team"] == "ops"


def test_set_owner_persisted(state_dir):
    set_owner(state_dir, "backup", "alice")
    rec = get_owner(state_dir, "backup")
    assert rec is not None
    assert rec["owner"] == "alice"


def test_set_owner_overwrites_existing(state_dir):
    set_owner(state_dir, "backup", "alice")
    set_owner(state_dir, "backup", "charlie")
    rec = get_owner(state_dir, "backup")
    assert rec["owner"] == "charlie"


def test_remove_owner_existing(state_dir):
    set_owner(state_dir, "backup", "alice")
    result = remove_owner(state_dir, "backup")
    assert result is True
    assert get_owner(state_dir, "backup") is None


def test_remove_owner_missing_returns_false(state_dir):
    assert remove_owner(state_dir, "nonexistent") is False


def test_list_owners_empty(state_dir):
    assert list_owners(state_dir) == []


def test_list_owners_sorted(state_dir):
    set_owner(state_dir, "zebra", "alice")
    set_owner(state_dir, "alpha", "bob")
    names = [r["job"] for r in list_owners(state_dir)]
    assert names == ["alpha", "zebra"]


def test_jobs_owned_by(state_dir):
    set_owner(state_dir, "backup", "alice")
    set_owner(state_dir, "cleanup", "bob")
    set_owner(state_dir, "report", "alice")
    owned = jobs_owned_by(state_dir, "alice")
    assert len(owned) == 2
    assert all(r["owner"] == "alice" for r in owned)


def test_jobs_owned_by_case_insensitive(state_dir):
    set_owner(state_dir, "backup", "Alice")
    owned = jobs_owned_by(state_dir, "alice")
    assert len(owned) == 1


def test_jobs_owned_by_no_match(state_dir):
    set_owner(state_dir, "backup", "alice")
    assert jobs_owned_by(state_dir, "nobody") == []


def test_jobs_owned_by_team(state_dir):
    set_owner(state_dir, "backup", "alice", team="ops")
    set_owner(state_dir, "cleanup", "bob", team="dev")
    set_owner(state_dir, "report", "carol", team="ops")
    result = jobs_owned_by_team(state_dir, "ops")
    assert len(result) == 2
    assert all(r["team"] == "ops" for r in result)


def test_jobs_owned_by_team_case_insensitive(state_dir):
    set_owner(state_dir, "backup", "alice", team="Ops")
    result = jobs_owned_by_team(state_dir, "ops")
    assert len(result) == 1


def test_jobs_owned_by_team_no_team_set(state_dir):
    set_owner(state_dir, "backup", "alice")  # no team
    result = jobs_owned_by_team(state_dir, "ops")
    assert result == []
