"""Tests for cronwatch.job_cooldown."""

from __future__ import annotations

import time
from datetime import datetime, timezone, timedelta
from unittest.mock import patch

import pytest

from cronwatch.job_cooldown import (
    set_cooldown,
    clear_cooldown,
    is_cooling_down,
    cooldown_remaining,
)


@pytest.fixture
def state_dir(tmp_path):
    return str(tmp_path)


NOW = datetime(2024, 6, 1, 12, 0, 0, tzinfo=timezone.utc)


def _now():
    return NOW


def test_is_cooling_down_no_entry_returns_false(state_dir):
    assert is_cooling_down(state_dir, "backup") is False


def test_set_cooldown_returns_record(state_dir):
    with patch("cronwatch.job_cooldown._utcnow", _now):
        record = set_cooldown(state_dir, "backup", 300)
    assert record["job"] == "backup"
    assert record["cooldown_seconds"] == 300
    assert "triggered_at" in record
    assert "expires_at" in record


def test_is_cooling_down_within_window(state_dir):
    with patch("cronwatch.job_cooldown._utcnow", _now):
        set_cooldown(state_dir, "backup", 300)
        assert is_cooling_down(state_dir, "backup") is True


def test_is_cooling_down_after_expiry(state_dir):
    with patch("cronwatch.job_cooldown._utcnow", _now):
        set_cooldown(state_dir, "backup", 300)

    future = NOW + timedelta(seconds=301)
    with patch("cronwatch.job_cooldown._utcnow", lambda: future):
        assert is_cooling_down(state_dir, "backup") is False


def test_cooldown_remaining_no_entry_returns_none(state_dir):
    assert cooldown_remaining(state_dir, "backup") is None


def test_cooldown_remaining_within_window(state_dir):
    with patch("cronwatch.job_cooldown._utcnow", _now):
        set_cooldown(state_dir, "backup", 300)

    check_time = NOW + timedelta(seconds=100)
    with patch("cronwatch.job_cooldown._utcnow", lambda: check_time):
        remaining = cooldown_remaining(state_dir, "backup")
    assert remaining is not None
    assert 199 < remaining <= 200


def test_cooldown_remaining_after_expiry_returns_none(state_dir):
    with patch("cronwatch.job_cooldown._utcnow", _now):
        set_cooldown(state_dir, "backup", 60)

    future = NOW + timedelta(seconds=120)
    with patch("cronwatch.job_cooldown._utcnow", lambda: future):
        assert cooldown_remaining(state_dir, "backup") is None


def test_clear_cooldown_removes_entry(state_dir):
    with patch("cronwatch.job_cooldown._utcnow", _now):
        set_cooldown(state_dir, "backup", 300)
        assert is_cooling_down(state_dir, "backup") is True
    clear_cooldown(state_dir, "backup")
    assert is_cooling_down(state_dir, "backup") is False


def test_clear_cooldown_returns_true_when_existed(state_dir):
    with patch("cronwatch.job_cooldown._utcnow", _now):
        set_cooldown(state_dir, "backup", 300)
    assert clear_cooldown(state_dir, "backup") is True


def test_clear_cooldown_returns_false_when_missing(state_dir):
    assert clear_cooldown(state_dir, "nonexistent") is False


def test_multiple_jobs_are_independent(state_dir):
    with patch("cronwatch.job_cooldown._utcnow", _now):
        set_cooldown(state_dir, "job_a", 300)
    assert is_cooling_down(state_dir, "job_a") is True
    assert is_cooling_down(state_dir, "job_b") is False
