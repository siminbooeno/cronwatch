"""Tests for cronwatch.labels."""
import pytest

from cronwatch.config import CronwatchConfig, JobConfig, AlertConfig
from cronwatch.labels import (
    jobs_with_label,
    jobs_matching_selector,
    all_label_keys,
    all_label_values,
    parse_selector,
)


def _make_config(*jobs: JobConfig) -> CronwatchConfig:
    alert = AlertConfig(webhook_url=None, email_to=None, email_from=None, smtp_host=None)
    return CronwatchConfig(jobs=list(jobs), alert=alert, state_dir="/tmp", history_dir="/tmp")


def _job(name: str, labels: dict) -> JobConfig:
    return JobConfig(
        name=name,
        command=f"echo {name}",
        interval_seconds=60,
        grace_seconds=10,
        timeout_seconds=None,
        tags=[],
        labels=labels,
    )


@pytest.fixture
def cfg():
    return _make_config(
        _job("backup", {"env": "prod", "team": "infra"}),
        _job("report", {"env": "prod", "team": "analytics"}),
        _job("cleanup", {"env": "staging", "team": "infra"}),
        _job("nolabel", {}),
    )


def test_jobs_with_label_returns_matching(cfg):
    result = jobs_with_label(cfg, "env", "prod")
    assert [j.name for j in result] == ["backup", "report"]


def test_jobs_with_label_no_match(cfg):
    result = jobs_with_label(cfg, "env", "dev")
    assert result == []


def test_jobs_with_label_missing_key(cfg):
    result = jobs_with_label(cfg, "owner", "alice")
    assert result == []


def test_jobs_matching_selector_single(cfg):
    result = jobs_matching_selector(cfg, {"team": "infra"})
    assert [j.name for j in result] == ["backup", "cleanup"]


def test_jobs_matching_selector_multi(cfg):
    result = jobs_matching_selector(cfg, {"env": "prod", "team": "infra"})
    assert [j.name for j in result] == ["backup"]


def test_jobs_matching_selector_empty_matches_all(cfg):
    result = jobs_matching_selector(cfg, {})
    assert len(result) == 4


def test_all_label_keys(cfg):
    assert all_label_keys(cfg) == ["env", "team"]


def test_all_label_values(cfg):
    assert all_label_values(cfg, "env") == ["prod", "staging"]
    assert all_label_values(cfg, "team") == ["analytics", "infra"]


def test_all_label_values_missing_key(cfg):
    assert all_label_values(cfg, "nonexistent") == []


def test_parse_selector_valid():
    assert parse_selector("env=prod,team=infra") == {"env": "prod", "team": "infra"}


def test_parse_selector_single():
    assert parse_selector("env=staging") == {"env": "staging"}


def test_parse_selector_empty_string():
    assert parse_selector("") == {}


def test_parse_selector_missing_equals_raises():
    with pytest.raises(ValueError, match="key=value"):
        parse_selector("envprod")


def test_parse_selector_empty_key_raises():
    with pytest.raises(ValueError, match="Empty key"):
        parse_selector("=prod")
