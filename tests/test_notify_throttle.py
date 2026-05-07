"""Tests for cronwatch.notify_throttle."""

from __future__ import annotations

import json
from datetime import datetime, timedelta, timezone
from pathlib import Path
from unittest.mock import patch

import pytest

from cronwatch.notify_throttle import (
    clear_throttle,
    is_throttled,
    prune_throttle,
    record_alert_sent,
)

_MODULE = "cronwatch.notify_throttle._utcnow"


@pytest.fixture()
def state_dir(tmp_path: Path) -> str:
    return str(tmp_path)


def _now() -> datetime:
    return datetime.now(timezone.utc)


# ---------------------------------------------------------------------------
# is_throttled
# ---------------------------------------------------------------------------

def test_not_throttled_when_no_entry(state_dir: str) -> None:
    assert is_throttled(state_dir, "backup", cooldown_seconds=300) is False


def test_throttled_within_cooldown(state_dir: str) -> None:
    now = _now()
    with patch(_MODULE, return_value=now):
        record_alert_sent(state_dir, "backup")
    # 10 seconds later — still within 300 s cooldown
    with patch(_MODULE, return_value=now + timedelta(seconds=10)):
        assert is_throttled(state_dir, "backup", cooldown_seconds=300) is True


def test_not_throttled_after_cooldown_expires(state_dir: str) -> None:
    now = _now()
    with patch(_MODULE, return_value=now):
        record_alert_sent(state_dir, "backup")
    # 301 seconds later — cooldown expired
    with patch(_MODULE, return_value=now + timedelta(seconds=301)):
        assert is_throttled(state_dir, "backup", cooldown_seconds=300) is False


# ---------------------------------------------------------------------------
# record_alert_sent
# ---------------------------------------------------------------------------

def test_record_alert_sent_writes_file(state_dir: str) -> None:
    record_alert_sent(state_dir, "myjob")
    data = json.loads((Path(state_dir) / "alert_throttle.json").read_text())
    assert "myjob" in data


def test_record_alert_sent_updates_timestamp(state_dir: str) -> None:
    t1 = _now()
    t2 = t1 + timedelta(minutes=5)
    with patch(_MODULE, return_value=t1):
        record_alert_sent(state_dir, "myjob")
    with patch(_MODULE, return_value=t2):
        record_alert_sent(state_dir, "myjob")
    data = json.loads((Path(state_dir) / "alert_throttle.json").read_text())
    stored = datetime.fromisoformat(data["myjob"])
    assert stored >= t2


# ---------------------------------------------------------------------------
# clear_throttle
# ---------------------------------------------------------------------------

def test_clear_throttle_removes_entry(state_dir: str) -> None:
    record_alert_sent(state_dir, "myjob")
    clear_throttle(state_dir, "myjob")
    assert is_throttled(state_dir, "myjob", cooldown_seconds=300) is False


def test_clear_throttle_noop_for_missing_entry(state_dir: str) -> None:
    clear_throttle(state_dir, "nonexistent")  # should not raise


# ---------------------------------------------------------------------------
# prune_throttle
# ---------------------------------------------------------------------------

def test_prune_removes_stale_entries(state_dir: str) -> None:
    old_time = _now() - timedelta(hours=25)
    with patch(_MODULE, return_value=old_time):
        record_alert_sent(state_dir, "old_job")
    record_alert_sent(state_dir, "new_job")
    removed = prune_throttle(state_dir, max_age_seconds=86400)
    assert removed == 1
    data = json.loads((Path(state_dir) / "alert_throttle.json").read_text())
    assert "old_job" not in data
    assert "new_job" in data


def test_prune_returns_zero_when_nothing_stale(state_dir: str) -> None:
    record_alert_sent(state_dir, "fresh_job")
    removed = prune_throttle(state_dir, max_age_seconds=86400)
    assert removed == 0
