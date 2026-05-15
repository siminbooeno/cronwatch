"""Tests for cronwatch.job_tags_summary."""
import json
from pathlib import Path
from datetime import datetime, timezone

import pytest

from cronwatch.config import CronwatchConfig, JobConfig, AlertConfig
from cronwatch.history import JobHistory
from cronwatch.job_tags_summary import build_tag_summaries, TagSummary


@pytest.fixture()
def history_dir(tmp_path: Path) -> Path:
    d = tmp_path / "history"
    d.mkdir()
    return d


def _make_config(*jobs: JobConfig) -> CronwatchConfig:
    alert = AlertConfig(webhook_url=None, email_to=None, email_from=None, smtp_host=None)
    return CronwatchConfig(jobs=list(jobs), alert=alert, state_dir="/tmp", history_dir="/tmp")


def _job(name: str, tags: list[str], interval: int = 60) -> JobConfig:
    return JobConfig(
        name=name,
        command=f"echo {name}",
        interval_seconds=interval,
        grace_seconds=10,
        timeout_seconds=None,
        tags=tags,
        labels={},
    )


def _add(history_dir: Path, job_name: str, success: bool) -> None:
    hist = JobHistory(job_name, history_dir)
    ts = datetime.now(timezone.utc).isoformat()
    hist.append({"timestamp": ts, "success": success, "duration": 1.0, "exit_code": 0 if success else 1})


def test_build_tag_summaries_empty_config(history_dir: Path) -> None:
    cfg = _make_config()
    result = build_tag_summaries(cfg, history_dir)
    assert result == {}


def test_build_tag_summaries_no_tags(history_dir: Path) -> None:
    cfg = _make_config(_job("backup", []))
    result = build_tag_summaries(cfg, history_dir)
    assert result == {}


def test_build_tag_summaries_single_tag_never_run(history_dir: Path) -> None:
    cfg = _make_config(_job("backup", ["infra"]))
    result = build_tag_summaries(cfg, history_dir)
    assert "infra" in result
    s = result["infra"]
    assert s.total_jobs == 1
    assert s.never_run_jobs == 1
    assert s.healthy_jobs == 0
    assert s.failing_jobs == 0
    assert s.avg_success_rate == 1.0


def test_build_tag_summaries_healthy_job(history_dir: Path) -> None:
    cfg = _make_config(_job("backup", ["infra"]))
    _add(history_dir, "backup", success=True)
    _add(history_dir, "backup", success=True)
    result = build_tag_summaries(cfg, history_dir)
    s = result["infra"]
    assert s.healthy_jobs == 1
    assert s.failing_jobs == 0
    assert s.avg_success_rate == pytest.approx(1.0)


def test_build_tag_summaries_failing_job(history_dir: Path) -> None:
    cfg = _make_config(_job("backup", ["infra"]))
    _add(history_dir, "backup", success=False)
    result = build_tag_summaries(cfg, history_dir)
    s = result["infra"]
    assert s.failing_jobs == 1
    assert s.healthy_jobs == 0


def test_build_tag_summaries_multiple_jobs_same_tag(history_dir: Path) -> None:
    cfg = _make_config(_job("a", ["team"]), _job("b", ["team"]))
    _add(history_dir, "a", success=True)
    _add(history_dir, "b", success=False)
    result = build_tag_summaries(cfg, history_dir)
    s = result["team"]
    assert s.total_jobs == 2
    assert s.healthy_jobs == 1
    assert s.failing_jobs == 1
    assert 0.0 < s.avg_success_rate < 1.0


def test_tag_summary_as_dict_keys() -> None:
    s = TagSummary(tag="x", total_jobs=1, healthy_jobs=1)
    d = s.as_dict()
    assert set(d.keys()) == {"tag", "total_jobs", "healthy_jobs", "failing_jobs", "never_run_jobs", "avg_success_rate", "job_names"}


def test_tag_summary_as_text() -> None:
    s = TagSummary(tag="prod", total_jobs=3, healthy_jobs=2, failing_jobs=1, avg_success_rate=0.8)
    text = s.as_text()
    assert "prod" in text
    assert "80.0%" in text
