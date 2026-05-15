"""Tests for cronwatch.job_locks."""

import os
import time
import pytest

from cronwatch.job_locks import (
    acquire_lock,
    release_lock,
    is_locked,
    lock_info,
)


@pytest.fixture
def state_dir(tmp_path):
    return str(tmp_path)


def test_acquire_lock_succeeds_when_no_lock(state_dir):
    assert acquire_lock(state_dir, "backup") is True


def test_acquire_lock_creates_lock_file(state_dir):
    acquire_lock(state_dir, "backup")
    info = lock_info(state_dir, "backup")
    assert info is not None
    assert info["job"] == "backup"
    assert info["pid"] == os.getpid()


def test_acquire_lock_fails_when_already_locked(state_dir):
    acquire_lock(state_dir, "backup")
    assert acquire_lock(state_dir, "backup") is False


def test_acquire_lock_different_jobs_independent(state_dir):
    assert acquire_lock(state_dir, "job_a") is True
    assert acquire_lock(state_dir, "job_b") is True


def test_acquire_lock_overwrites_stale_lock(state_dir, monkeypatch):
    # Acquire with a very short TTL
    acquire_lock(state_dir, "backup", ttl_seconds=1)
    # Advance time past TTL
    original = time.time
    monkeypatch.setattr("cronwatch.job_locks._utcnow", lambda: original() + 10)
    assert acquire_lock(state_dir, "backup", ttl_seconds=1) is True


def test_release_lock_returns_true_when_exists(state_dir):
    acquire_lock(state_dir, "backup")
    assert release_lock(state_dir, "backup") is True


def test_release_lock_returns_false_when_missing(state_dir):
    assert release_lock(state_dir, "backup") is False


def test_release_lock_removes_file(state_dir):
    acquire_lock(state_dir, "backup")
    release_lock(state_dir, "backup")
    assert lock_info(state_dir, "backup") is None


def test_is_locked_false_when_no_lock(state_dir):
    assert is_locked(state_dir, "backup") is False


def test_is_locked_true_after_acquire(state_dir):
    acquire_lock(state_dir, "backup")
    assert is_locked(state_dir, "backup") is True


def test_is_locked_false_after_release(state_dir):
    acquire_lock(state_dir, "backup")
    release_lock(state_dir, "backup")
    assert is_locked(state_dir, "backup") is False


def test_is_locked_false_for_stale_lock(state_dir, monkeypatch):
    acquire_lock(state_dir, "backup", ttl_seconds=5)
    monkeypatch.setattr("cronwatch.job_locks._utcnow", lambda: time.time() + 100)
    assert is_locked(state_dir, "backup", ttl_seconds=5) is False


def test_lock_info_returns_none_when_missing(state_dir):
    assert lock_info(state_dir, "missing") is None


def test_lock_info_contains_ttl(state_dir):
    acquire_lock(state_dir, "backup", ttl_seconds=120)
    info = lock_info(state_dir, "backup")
    assert info["ttl_seconds"] == 120
