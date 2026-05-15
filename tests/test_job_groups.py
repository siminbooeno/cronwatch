"""Tests for cronwatch.job_groups and cronwatch.cli_job_groups."""
from __future__ import annotations

import json
import os
import pytest

from cronwatch.job_groups import (
    JobGroup,
    all_group_names,
    find_group,
    groups_for_job,
    jobs_in_group,
    load_groups,
)
from cronwatch.config import CronwatchConfig, JobConfig, AlertConfig
from cronwatch.cli_job_groups import cmd_list, cmd_show, cmd_membership, _build_parser


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture()
def groups_file(tmp_path):
    data = {
        "groups": [
            {"name": "critical", "jobs": ["backup", "report"], "description": "Must not fail"},
            {"name": "nightly", "jobs": ["report", "cleanup"]},
        ]
    }
    p = tmp_path / "groups.json"
    p.write_text(json.dumps(data))
    return str(p)


def _make_config():
    alert = AlertConfig(email=None, webhook_url=None)
    jobs = [
        JobConfig(name="backup", command="/bin/backup", interval_seconds=3600, grace_seconds=60),
        JobConfig(name="report", command="/bin/report", interval_seconds=86400, grace_seconds=300),
        JobConfig(name="cleanup", command="/bin/cleanup", interval_seconds=86400, grace_seconds=300),
    ]
    return CronwatchConfig(jobs=jobs, alert=alert, state_dir="/tmp", history_dir="/tmp")


# ---------------------------------------------------------------------------
# load_groups
# ---------------------------------------------------------------------------

def test_load_groups_returns_list(groups_file):
    groups = load_groups(groups_file)
    assert len(groups) == 2


def test_load_groups_missing_file(tmp_path):
    result = load_groups(str(tmp_path / "nope.json"))
    assert result == []


def test_load_groups_fields(groups_file):
    groups = load_groups(groups_file)
    critical = find_group(groups, "critical")
    assert critical is not None
    assert critical.description == "Must not fail"
    assert "backup" in critical.job_names


# ---------------------------------------------------------------------------
# Query helpers
# ---------------------------------------------------------------------------

def test_jobs_in_group(groups_file):
    groups = load_groups(groups_file)
    cfg = _make_config()
    nightly = find_group(groups, "nightly")
    jobs = jobs_in_group(nightly, cfg)
    assert {j.name for j in jobs} == {"report", "cleanup"}


def test_groups_for_job(groups_file):
    groups = load_groups(groups_file)
    matched = groups_for_job(groups, "report")
    assert {g.name for g in matched} == {"critical", "nightly"}


def test_groups_for_job_no_match(groups_file):
    groups = load_groups(groups_file)
    assert groups_for_job(groups, "unknown") == []


def test_all_group_names(groups_file):
    groups = load_groups(groups_file)
    assert all_group_names(groups) == ["critical", "nightly"]


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

class _Args:
    def __init__(self, **kwargs):
        for k, v in kwargs.items():
            setattr(self, k, v)


def test_cmd_list(groups_file, capsys):
    args = _Args(groups_file=groups_file)
    rc = cmd_list(args)
    assert rc == 0
    out = capsys.readouterr().out
    assert "critical" in out
    assert "nightly" in out


def test_cmd_show_unknown_group(groups_file, capsys):
    cfg_obj = _make_config()
    # write a temp config file
    import tempfile
    args = _Args(groups_file=groups_file, group="missing", config="")
    rc = cmd_show(args)
    assert rc == 1


def test_cmd_membership_found(groups_file, capsys):
    args = _Args(groups_file=groups_file, job="report")
    rc = cmd_membership(args)
    assert rc == 0
    out = capsys.readouterr().out
    assert "critical" in out
    assert "nightly" in out


def test_cmd_membership_not_found(groups_file, capsys):
    args = _Args(groups_file=groups_file, job="ghost")
    rc = cmd_membership(args)
    assert rc == 0
    out = capsys.readouterr().out
    assert "not in any group" in out
