"""Tests for cronwatch.job_badges."""
from __future__ import annotations

import json
import os
from pathlib import Path

import pytest

from cronwatch.history import JobHistory
from cronwatch.job_badges import Badge, build_badge, _success_rate_color
from cronwatch.pauses import pause_job


@pytest.fixture()
def dirs(tmp_path: Path):
    history = tmp_path / "history"
    state = tmp_path / "state"
    history.mkdir()
    state.mkdir()
    return str(history), str(state)


def _add(history_dir: str, job: str, *, success: bool):
    h = JobHistory(job, history_dir=history_dir)
    if success:
        h.add(success=True, duration=1.0, exit_code=0)
    else:
        h.add(success=False, duration=1.0, exit_code=1)


# --- Badge.as_dict ---

def test_badge_as_dict_keys():
    b = Badge("myjob", "myjob", "5/5 passing", "brightgreen")
    d = b.as_dict()
    assert d["schemaVersion"] == 1
    assert d["label"] == "myjob"
    assert d["message"] == "5/5 passing"
    assert d["color"] == "brightgreen"


def test_badge_as_text():
    b = Badge("myjob", "myjob", "5/5 passing", "brightgreen")
    assert "brightgreen" in b.as_text()
    assert "5/5 passing" in b.as_text()


# --- _success_rate_color ---

def test_color_high_rate():
    assert _success_rate_color(1.0) == "brightgreen"
    assert _success_rate_color(0.95) == "brightgreen"


def test_color_mid_rate():
    assert _success_rate_color(0.85) == "orange"
    assert _success_rate_color(0.80) == "orange"


def test_color_low_rate():
    assert _success_rate_color(0.79) == "red"
    assert _success_rate_color(0.0) == "red"


# --- build_badge ---

def test_build_badge_no_history_returns_unknown(dirs):
    history_dir, state_dir = dirs
    badge = build_badge("backup", history_dir, state_dir)
    assert badge.message == "unknown"
    assert badge.color == "lightgrey"


def test_build_badge_all_success(dirs):
    history_dir, state_dir = dirs
    for _ in range(5):
        _add(history_dir, "backup", success=True)
    badge = build_badge("backup", history_dir, state_dir)
    assert "5/5" in badge.message
    assert badge.color == "brightgreen"


def test_build_badge_mixed(dirs):
    history_dir, state_dir = dirs
    for _ in range(8):
        _add(history_dir, "sync", success=True)
    for _ in range(2):
        _add(history_dir, "sync", success=False)
    badge = build_badge("sync", history_dir, state_dir)
    assert "8/10" in badge.message


def test_build_badge_paused(dirs):
    history_dir, state_dir = dirs
    for _ in range(5):
        _add(history_dir, "report", success=True)
    pause_job("report", state_dir=state_dir)
    badge = build_badge("report", history_dir, state_dir)
    assert badge.message == "paused"
    assert badge.color == "yellow"


def test_build_badge_custom_label(dirs):
    history_dir, state_dir = dirs
    _add(history_dir, "etl", success=True)
    badge = build_badge("etl", history_dir, state_dir, label="ETL Job")
    assert badge.label == "ETL Job"
    assert badge.job_name == "etl"
