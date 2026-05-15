"""Tests for cronwatch.oncall and cronwatch.cli_oncall."""

from __future__ import annotations

import pytest

from cronwatch.oncall import (
    get_oncall_contacts,
    list_oncall,
    remove_oncall,
    set_oncall,
)
from cronwatch.cli_oncall import (
    _build_parser,
    cmd_list,
    cmd_query,
    cmd_remove,
    cmd_set,
)


@pytest.fixture()
def state_dir(tmp_path):
    return str(tmp_path)


def test_set_oncall_creates_entry(state_dir):
    entry = set_oncall(state_dir, "ops@example.com")
    assert entry.contact == "ops@example.com"
    assert entry.jobs == []
    assert entry.tags == []


def test_set_oncall_with_jobs_and_tags(state_dir):
    entry = set_oncall(state_dir, "dev@example.com",
                       jobs=["backup"], tags=["critical"], note="primary")
    assert entry.jobs == ["backup"]
    assert entry.tags == ["critical"]
    assert entry.note == "primary"


def test_set_oncall_overwrites_existing(state_dir):
    set_oncall(state_dir, "ops@example.com", jobs=["job-a"])
    set_oncall(state_dir, "ops@example.com", jobs=["job-b"])
    entries = list_oncall(state_dir)
    assert len(entries) == 1
    assert entries[0].jobs == ["job-b"]


def test_remove_oncall_existing(state_dir):
    set_oncall(state_dir, "ops@example.com")
    assert remove_oncall(state_dir, "ops@example.com") is True
    assert list_oncall(state_dir) == []


def test_remove_oncall_missing_returns_false(state_dir):
    assert remove_oncall(state_dir, "nobody@example.com") is False


def test_get_contacts_global_entry(state_dir):
    set_oncall(state_dir, "ops@example.com")
    contacts = get_oncall_contacts(state_dir, "any-job")
    assert "ops@example.com" in contacts


def test_get_contacts_job_specific(state_dir):
    set_oncall(state_dir, "dev@example.com", jobs=["backup"])
    set_oncall(state_dir, "ops@example.com", jobs=["deploy"])
    assert "dev@example.com" in get_oncall_contacts(state_dir, "backup")
    assert "ops@example.com" not in get_oncall_contacts(state_dir, "backup")


def test_get_contacts_tag_match(state_dir):
    set_oncall(state_dir, "sec@example.com", tags=["security"])
    contacts = get_oncall_contacts(state_dir, "scan-job", job_tags=["security", "nightly"])
    assert "sec@example.com" in contacts


def test_get_contacts_tag_no_match(state_dir):
    set_oncall(state_dir, "sec@example.com", tags=["security"])
    contacts = get_oncall_contacts(state_dir, "backup", job_tags=["nightly"])
    assert "sec@example.com" not in contacts


def test_list_oncall_empty(state_dir):
    assert list_oncall(state_dir) == []


# --- CLI tests ---

class _Args:
    def __init__(self, **kw):
        self.__dict__.update(kw)


def test_cmd_set_prints_contact(state_dir, capsys):
    args = _Args(state_dir=state_dir, contact="ops@example.com",
                 jobs=[], tags=[], note="")
    rc = cmd_set(args)
    assert rc == 0
    assert "ops@example.com" in capsys.readouterr().out


def test_cmd_remove_success(state_dir, capsys):
    set_oncall(state_dir, "ops@example.com")
    args = _Args(state_dir=state_dir, contact="ops@example.com")
    assert cmd_remove(args) == 0


def test_cmd_remove_missing_returns_1(state_dir):
    args = _Args(state_dir=state_dir, contact="ghost@example.com")
    assert cmd_remove(args) == 1


def test_cmd_list_no_entries(state_dir, capsys):
    args = _Args(state_dir=state_dir, as_json=False)
    rc = cmd_list(args)
    assert rc == 0
    assert "No on-call" in capsys.readouterr().out


def test_cmd_list_json(state_dir, capsys):
    set_oncall(state_dir, "ops@example.com")
    args = _Args(state_dir=state_dir, as_json=True)
    cmd_list(args)
    import json
    data = json.loads(capsys.readouterr().out)
    assert data[0]["contact"] == "ops@example.com"


def test_cmd_query_with_match(state_dir, capsys):
    set_oncall(state_dir, "ops@example.com", jobs=["backup"])
    args = _Args(state_dir=state_dir, job="backup", tags=[])
    rc = cmd_query(args)
    assert rc == 0
    assert "ops@example.com" in capsys.readouterr().out


def test_cmd_query_no_match(state_dir, capsys):
    args = _Args(state_dir=state_dir, job="unknown", tags=[])
    rc = cmd_query(args)
    assert rc == 0
    assert "No on-call" in capsys.readouterr().out
