"""Tests for cronwatch.job_search."""
from __future__ import annotations

import pytest

from cronwatch.config import CronwatchConfig, JobConfig, AlertConfig
from cronwatch.job_search import SearchResult, find_job_by_name, search_jobs


def _make_config(*jobs: JobConfig) -> CronwatchConfig:
    alert = AlertConfig(webhook_url=None, email_to=None, email_from=None, smtp_host=None)
    return CronwatchConfig(jobs=list(jobs), alert=alert, state_dir="/tmp")


def _job(name="backup", command="/usr/bin/backup", tags=None, labels=None) -> JobConfig:
    return JobConfig(
        name=name,
        command=command,
        interval_seconds=3600,
        grace_seconds=300,
        timeout_seconds=None,
        tags=tags or [],
        labels=labels or {},
    )


# --- search_jobs ---

def test_search_jobs_matches_name():
    cfg = _make_config(_job(name="db-backup"), _job(name="log-rotate"))
    results = search_jobs(cfg, "backup")
    assert len(results) == 1
    assert results[0].job.name == "db-backup"
    assert "name" in results[0].matched_fields


def test_search_jobs_matches_command():
    cfg = _make_config(_job(command="/opt/scripts/cleanup.sh"), _job(command="/bin/true"))
    results = search_jobs(cfg, "cleanup")
    assert len(results) == 1
    assert "command" in results[0].matched_fields


def test_search_jobs_matches_tag():
    cfg = _make_config(
        _job(name="a", tags=["production", "db"]),
        _job(name="b", tags=["staging"]),
    )
    results = search_jobs(cfg, "production")
    assert len(results) == 1
    assert "tags" in results[0].matched_fields


def test_search_jobs_matches_label_key():
    cfg = _make_config(_job(name="a", labels={"env": "prod"}), _job(name="b"))
    results = search_jobs(cfg, "env")
    assert len(results) == 1
    assert "labels" in results[0].matched_fields


def test_search_jobs_matches_label_value():
    cfg = _make_config(_job(name="a", labels={"team": "platform"}))
    results = search_jobs(cfg, "platform")
    assert len(results) == 1


def test_search_jobs_no_match_returns_empty():
    cfg = _make_config(_job(name="hourly-sync"))
    results = search_jobs(cfg, "zzznomatch")
    assert results == []


def test_search_jobs_case_insensitive():
    cfg = _make_config(_job(name="DailyReport"))
    results = search_jobs(cfg, "daily")
    assert len(results) == 1


def test_search_jobs_restricted_fields():
    cfg = _make_config(_job(name="backup", command="/bin/backup"))
    # searching only 'command' should not match via 'name'
    results = search_jobs(cfg, "backup", fields=["command"])
    assert len(results) == 1
    assert results[0].matched_fields == ["command"]


def test_search_result_as_dict():
    job = _job(name="myjob", command="/bin/myjob")
    r = SearchResult(job=job, matched_fields=["name"])
    d = r.as_dict()
    assert d["name"] == "myjob"
    assert d["command"] == "/bin/myjob"
    assert d["matched_fields"] == ["name"]


# --- find_job_by_name ---

def test_find_job_by_name_exact():
    cfg = _make_config(_job(name="alpha"), _job(name="beta"))
    result = find_job_by_name(cfg, "alpha")
    assert result is not None
    assert result.name == "alpha"


def test_find_job_by_name_case_insensitive():
    cfg = _make_config(_job(name="Alpha"))
    result = find_job_by_name(cfg, "alpha")
    assert result is not None


def test_find_job_by_name_missing_returns_none():
    cfg = _make_config(_job(name="alpha"))
    result = find_job_by_name(cfg, "gamma")
    assert result is None
