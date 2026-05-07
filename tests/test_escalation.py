"""Tests for cronwatch.escalation module."""

import json
import os
import pytest
from unittest.mock import patch, MagicMock
from pathlib import Path

from cronwatch.config import JobConfig, AlertConfig
from cronwatch.escalation import (
    EscalationPolicy,
    parse_escalation_policies,
    check_and_escalate,
)
from cronwatch.history import JobHistory


@pytest.fixture()
def history_dir(tmp_path: Path) -> str:
    return str(tmp_path / "history")


def _make_job(name: str = "backup") -> JobConfig:
    return JobConfig(name=name, command="echo hi", interval=3600)


def _make_alert_raw(**kwargs) -> dict:
    base = {"webhook_url": "http://hooks.example.com/test"}
    base.update(kwargs)
    return base


# --- parse_escalation_policies ---

def test_parse_empty_returns_empty():
    assert parse_escalation_policies({}) == []


def test_parse_single_policy():
    raw = {
        "escalations": [
            {"threshold": 5, "alert": _make_alert_raw(), "reason": "ops team"}
        ]
    }
    policies = parse_escalation_policies(raw)
    assert len(policies) == 1
    assert policies[0].threshold == 5
    assert policies[0].reason == "ops team"
    assert policies[0].alert.webhook_url == "http://hooks.example.com/test"


def test_parse_multiple_policies():
    raw = {
        "escalations": [
            {"threshold": 3, "alert": _make_alert_raw()},
            {"threshold": 10, "alert": _make_alert_raw(webhook_url="http://other")},
        ]
    }
    policies = parse_escalation_policies(raw)
    assert len(policies) == 2
    assert policies[0].threshold == 3
    assert policies[1].threshold == 10


def test_parse_default_threshold():
    raw = {"escalations": [{"alert": _make_alert_raw()}]}
    policies = parse_escalation_policies(raw)
    assert policies[0].threshold == 3


# --- check_and_escalate ---

def test_no_policies_returns_empty(history_dir):
    job = _make_job()
    result = check_and_escalate(job, [], history_dir)
    assert result == []


def test_escalation_not_triggered_below_threshold(history_dir):
    job = _make_job("sync")
    hist = JobHistory(job.name, history_dir)
    hist.add(success=False)
    hist.add(success=False)  # 2 consecutive failures

    policy = EscalationPolicy(
        threshold=5,
        alert=AlertConfig(webhook_url="http://example.com"),
    )
    with patch("cronwatch.escalation.dispatch_alert") as mock_dispatch:
        triggered = check_and_escalate(job, [policy], history_dir)
    assert triggered == []
    mock_dispatch.assert_not_called()


def test_escalation_triggered_at_threshold(history_dir):
    job = _make_job("deploy")
    hist = JobHistory(job.name, history_dir)
    for _ in range(3):
        hist.add(success=False)

    policy = EscalationPolicy(
        threshold=3,
        alert=AlertConfig(webhook_url="http://escalate.example.com"),
        reason="critical job",
    )
    with patch("cronwatch.escalation.dispatch_alert") as mock_dispatch:
        triggered = check_and_escalate(job, [policy], history_dir)

    assert len(triggered) == 1
    assert triggered[0] is policy
    mock_dispatch.assert_called_once()
    call_args = mock_dispatch.call_args
    assert "ESCALATION" in call_args[0][1] or "ESCALATION" in call_args[0][2]


def test_multiple_policies_only_matching_triggered(history_dir):
    job = _make_job("etl")
    hist = JobHistory(job.name, history_dir)
    for _ in range(4):
        hist.add(success=False)

    low = EscalationPolicy(threshold=3, alert=AlertConfig(webhook_url="http://low"))
    high = EscalationPolicy(threshold=10, alert=AlertConfig(webhook_url="http://high"))

    with patch("cronwatch.escalation.dispatch_alert") as mock_dispatch:
        triggered = check_and_escalate(job, [low, high], history_dir)

    assert triggered == [low]
    assert mock_dispatch.call_count == 1
