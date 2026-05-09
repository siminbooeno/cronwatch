"""Tests for cronwatch.rate_limit."""

from __future__ import annotations

import json
from datetime import datetime, timedelta, timezone
from pathlib import Path
from unittest.mock import patch

import pytest

from cronwatch.rate_limit import (
    _rate_limit_path,
    _utcnow,
    reset_rate_limit,
    should_send_alert,
)

JOB = "my_job"
MAX = 3
WINDOW = 3600  # 1 hour


@pytest.fixture()
def state_dir(tmp_path: Path) -> str:
    return str(tmp_path)


def test_first_alert_is_allowed(state_dir: str) -> None:
    assert should_send_alert(state_dir, JOB, MAX, WINDOW) is True


def test_alerts_allowed_up_to_max(state_dir: str) -> None:
    for _ in range(MAX):
        assert should_send_alert(state_dir, JOB, MAX, WINDOW) is True


def test_alert_suppressed_after_max(state_dir: str) -> None:
    for _ in range(MAX):
        should_send_alert(state_dir, JOB, MAX, WINDOW)
    assert should_send_alert(state_dir, JOB, MAX, WINDOW) is False


def test_suppressed_count_increments(state_dir: str) -> None:
    for _ in range(MAX):
        should_send_alert(state_dir, JOB, MAX, WINDOW)
    should_send_alert(state_dir, JOB, MAX, WINDOW)
    should_send_alert(state_dir, JOB, MAX, WINDOW)

    path = _rate_limit_path(state_dir, JOB)
    data = json.loads(path.read_text())
    assert data["suppressed_count"] == 2


def test_window_expiry_resets_state(state_dir: str) -> None:
    now = datetime.now(timezone.utc)
    past = now - timedelta(seconds=WINDOW + 1)

    with patch("cronwatch.rate_limit._utcnow", return_value=past):
        for _ in range(MAX):
            should_send_alert(state_dir, JOB, MAX, WINDOW)

    # Window has expired — should be allowed again
    assert should_send_alert(state_dir, JOB, MAX, WINDOW) is True


def test_reset_clears_state_file(state_dir: str) -> None:
    should_send_alert(state_dir, JOB, MAX, WINDOW)
    path = _rate_limit_path(state_dir, JOB)
    assert path.exists()

    reset_rate_limit(state_dir, JOB)
    assert not path.exists()


def test_reset_nonexistent_is_noop(state_dir: str) -> None:
    reset_rate_limit(state_dir, JOB)  # should not raise


def test_state_dir_created_if_missing(tmp_path: Path) -> None:
    missing = str(tmp_path / "new" / "subdir")
    assert should_send_alert(missing, JOB, MAX, WINDOW) is True
    assert Path(missing).exists()


def test_job_name_with_spaces(state_dir: str) -> None:
    job = "my job with spaces"
    assert should_send_alert(state_dir, job, MAX, WINDOW) is True
    path = _rate_limit_path(state_dir, job)
    assert " " not in path.name
