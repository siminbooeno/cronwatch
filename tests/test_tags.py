"""Tests for cronwatch.tags tag-filtering helpers."""
from __future__ import annotations

import pytest

from cronwatch.config import AlertConfig, CronwatchConfig, JobConfig
from cronwatch.tags import all_tags, filter_jobs, jobs_with_tag, jobs_without_tag


def _make_config(*jobs: JobConfig) -> CronwatchConfig:
    return CronwatchConfig(jobs=list(jobs), alert=AlertConfig())


def _job(name: str, tags: list[str] | None = None) -> JobConfig:
    return JobConfig(
        name=name,
        command=f"echo {name}",
        interval_seconds=3600,
        tags=tags or [],
    )


@pytest.fixture()
def cfg() -> CronwatchConfig:
    return _make_config(
        _job("backup", ["backup", "critical"]),
        _job("sync", ["sync"]),
        _job("ping", ["monitoring", "critical"]),
        _job("untagged"),
    )


def test_jobs_with_tag_returns_matching(cfg: CronwatchConfig) -> None:
    result = jobs_with_tag(cfg, "critical")
    assert {j.name for j in result} == {"backup", "ping"}


def test_jobs_with_tag_no_match(cfg: CronwatchConfig) -> None:
    assert jobs_with_tag(cfg, "nonexistent") == []


def test_jobs_without_tag_excludes_matching(cfg: CronwatchConfig) -> None:
    result = jobs_without_tag(cfg, "critical")
    assert {j.name for j in result} == {"sync", "untagged"}


def test_filter_jobs_include_single_tag(cfg: CronwatchConfig) -> None:
    result = filter_jobs(cfg, include=["backup"])
    assert [j.name for j in result] == ["backup"]


def test_filter_jobs_include_multiple_tags_all_required(cfg: CronwatchConfig) -> None:
    # only "backup" has both backup AND critical
    result = filter_jobs(cfg, include=["backup", "critical"])
    assert [j.name for j in result] == ["backup"]


def test_filter_jobs_exclude_tag(cfg: CronwatchConfig) -> None:
    result = filter_jobs(cfg, exclude=["critical"])
    assert {j.name for j in result} == {"sync", "untagged"}


def test_filter_jobs_include_and_exclude(cfg: CronwatchConfig) -> None:
    # include critical, but exclude monitoring
    result = filter_jobs(cfg, include=["critical"], exclude=["monitoring"])
    assert [j.name for j in result] == ["backup"]


def test_filter_jobs_no_filters_returns_all(cfg: CronwatchConfig) -> None:
    result = filter_jobs(cfg)
    assert len(result) == 4


def test_all_tags_sorted_unique(cfg: CronwatchConfig) -> None:
    tags = all_tags(cfg)
    assert tags == ["backup", "critical", "monitoring", "sync"]


def test_all_tags_empty_config() -> None:
    cfg = _make_config(_job("no-tags"))
    assert all_tags(cfg) == []
