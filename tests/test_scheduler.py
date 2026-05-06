"""Tests for cronwatch.scheduler."""

from __future__ import annotations

from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from cronwatch.config import AlertConfig, CronwatchConfig, JobConfig
from cronwatch.scheduler import run_scheduler


@pytest.fixture()
def tmp_state(tmp_path: Path) -> Path:
    return tmp_path / "state"


def _make_config(jobs: list[JobConfig] | None = None) -> CronwatchConfig:
    return CronwatchConfig(
        jobs=jobs or [],
        alert=AlertConfig(webhook_url=None, email=None),
    )


def test_run_scheduler_once_no_jobs(tmp_state: Path) -> None:
    """Scheduler with no jobs completes without error."""
    config = _make_config()
    run_scheduler(config, tmp_state, poll_interval=1, once=True)


def test_run_scheduler_once_no_overdue(tmp_state: Path) -> None:
    """No overdue jobs → dispatch_alert is never called."""
    job = JobConfig(name="backup", command="true", interval=3600, grace=60)
    config = _make_config([job])

    with patch("cronwatch.scheduler.check_jobs", return_value=[]) as mock_check, \
         patch("cronwatch.scheduler.dispatch_alert") as mock_alert:
        run_scheduler(config, tmp_state, poll_interval=1, once=True)

    mock_check.assert_called_once_with(config.jobs, tmp_state)
    mock_alert.assert_not_called()


def test_run_scheduler_once_with_overdue_dispatches_alert(tmp_state: Path) -> None:
    """Overdue jobs trigger dispatch_alert for each entry."""
    job = JobConfig(name="sync", command="sync.sh", interval=300, grace=30)
    config = _make_config([job])

    overdue = [("sync", "last seen 10 minutes ago")]

    with patch("cronwatch.scheduler.check_jobs", return_value=overdue), \
         patch("cronwatch.scheduler.dispatch_alert") as mock_alert:
        run_scheduler(config, tmp_state, poll_interval=1, once=True)

    mock_alert.assert_called_once_with(
        config.alert,
        job_name="sync",
        event="miss",
        detail="last seen 10 minutes ago",
    )


def test_run_scheduler_once_multiple_overdue(tmp_state: Path) -> None:
    """Each overdue job gets its own alert dispatch."""
    jobs = [
        JobConfig(name="a", command="a.sh", interval=60, grace=10),
        JobConfig(name="b", command="b.sh", interval=60, grace=10),
    ]
    config = _make_config(jobs)
    overdue = [("a", "overdue"), ("b", "overdue")]

    with patch("cronwatch.scheduler.check_jobs", return_value=overdue), \
         patch("cronwatch.scheduler.dispatch_alert") as mock_alert:
        run_scheduler(config, tmp_state, poll_interval=1, once=True)

    assert mock_alert.call_count == 2
