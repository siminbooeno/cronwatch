"""Tests for cronwatch.report — periodic digest report dispatch."""

from __future__ import annotations

import datetime
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from cronwatch.config import AlertConfig, CronwatchConfig, JobConfig
from cronwatch.report import (
    _read_last_report_time,
    _write_last_report_time,
    is_report_due,
    maybe_send_digest,
    send_digest_report,
)


_NOW = datetime.datetime(2024, 6, 1, 12, 0, 0, tzinfo=datetime.timezone.utc)


@pytest.fixture()
def state_dir(tmp_path: Path) -> Path:
    d = tmp_path / "state"
    d.mkdir()
    return d


@pytest.fixture()
def history_dir(tmp_path: Path) -> Path:
    d = tmp_path / "history"
    d.mkdir()
    return d


def _make_cfg() -> CronwatchConfig:
    job = JobConfig(name="backup", command="tar -czf /tmp/b.tgz /data", interval=3600)
    alert = AlertConfig(webhook_url="https://hooks.example.com/test")
    return CronwatchConfig(jobs=[job], alert=alert)


# --- timestamp helpers ---

def test_read_last_report_time_missing(state_dir: Path) -> None:
    assert _read_last_report_time(state_dir) is None


def test_write_and_read_last_report_time(state_dir: Path) -> None:
    _write_last_report_time(state_dir, _NOW)
    result = _read_last_report_time(state_dir)
    assert result == _NOW


def test_read_last_report_time_corrupt(state_dir: Path) -> None:
    (state_dir / ".last_report").write_text("not-a-date")
    assert _read_last_report_time(state_dir) is None


# --- is_report_due ---

def test_is_report_due_no_previous(state_dir: Path) -> None:
    assert is_report_due(state_dir, interval_hours=24) is True


def test_is_report_due_recent(state_dir: Path) -> None:
    recent = _NOW - datetime.timedelta(hours=1)
    _write_last_report_time(state_dir, recent)
    with patch("cronwatch.report._utcnow", return_value=_NOW):
        assert is_report_due(state_dir, interval_hours=24) is False


def test_is_report_due_elapsed(state_dir: Path) -> None:
    old = _NOW - datetime.timedelta(hours=25)
    _write_last_report_time(state_dir, old)
    with patch("cronwatch.report._utcnow", return_value=_NOW):
        assert is_report_due(state_dir, interval_hours=24) is True


# --- send_digest_report / maybe_send_digest ---

def test_send_digest_report_dispatches_alert(state_dir: Path, history_dir: Path) -> None:
    cfg = _make_cfg()
    with patch("cronwatch.report.dispatch_alert") as mock_dispatch, \
         patch("cronwatch.report._utcnow", return_value=_NOW):
        send_digest_report(cfg, state_dir, history_dir)
        mock_dispatch.assert_called_once()
        call_kwargs = mock_dispatch.call_args
        assert "subject" in call_kwargs.kwargs
        assert "cronwatch" in call_kwargs.kwargs["subject"]


def test_maybe_send_digest_sends_when_due(state_dir: Path, history_dir: Path) -> None:
    cfg = _make_cfg()
    with patch("cronwatch.report.dispatch_alert"), \
         patch("cronwatch.report._utcnow", return_value=_NOW):
        sent = maybe_send_digest(cfg, state_dir, history_dir, interval_hours=24)
    assert sent is True


def test_maybe_send_digest_skips_when_not_due(state_dir: Path, history_dir: Path) -> None:
    cfg = _make_cfg()
    recent = _NOW - datetime.timedelta(hours=1)
    _write_last_report_time(state_dir, recent)
    with patch("cronwatch.report.dispatch_alert") as mock_dispatch, \
         patch("cronwatch.report._utcnow", return_value=_NOW):
        sent = maybe_send_digest(cfg, state_dir, history_dir, interval_hours=24)
    assert sent is False
    mock_dispatch.assert_not_called()
