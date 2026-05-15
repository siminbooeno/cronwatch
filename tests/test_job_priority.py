"""Tests for cronwatch.job_priority."""
from __future__ import annotations

import pytest

from cronwatch.job_priority import (
    PriorityPolicy,
    _parse_priority,
    parse_priority_policies,
    priority_value,
    should_alert,
    jobs_by_priority,
    DEFAULT_PRIORITY,
)


# ---------------------------------------------------------------------------
# helpers
# ---------------------------------------------------------------------------

class _FakeJob:
    def __init__(self, name, priority_raw=None):
        self.name = name
        self.raw = {"priority": priority_raw} if priority_raw else {}


class _FakeCfg:
    def __init__(self, jobs):
        self.jobs = jobs


# ---------------------------------------------------------------------------
# _parse_priority
# ---------------------------------------------------------------------------

def test_parse_priority_defaults():
    pol = _parse_priority({})
    assert pol.level == DEFAULT_PRIORITY
    assert pol.alert_on_miss is True
    assert pol.alert_on_failure is True
    assert pol.min_failures_before_alert == 1


def test_parse_priority_full():
    pol = _parse_priority({"level": "low", "alert_on_miss": False, "min_failures_before_alert": 3})
    assert pol.level == "low"
    assert pol.alert_on_miss is False
    assert pol.min_failures_before_alert == 3


def test_parse_priority_invalid_level():
    with pytest.raises(ValueError, match="Unknown priority level"):
        _parse_priority({"level": "urgent"})


# ---------------------------------------------------------------------------
# priority_value ordering
# ---------------------------------------------------------------------------

def test_priority_value_ordering():
    assert priority_value(PriorityPolicy(level="critical")) < priority_value(PriorityPolicy(level="high"))
    assert priority_value(PriorityPolicy(level="high")) < priority_value(PriorityPolicy(level="medium"))
    assert priority_value(PriorityPolicy(level="medium")) < priority_value(PriorityPolicy(level="low"))


# ---------------------------------------------------------------------------
# should_alert
# ---------------------------------------------------------------------------

def test_should_alert_miss_suppressed():
    pol = PriorityPolicy(level="low", alert_on_miss=False)
    assert should_alert(pol, "miss") is False


def test_should_alert_failure_suppressed():
    pol = PriorityPolicy(level="low", alert_on_failure=False)
    assert should_alert(pol, "failure") is False


def test_should_alert_below_min_failures():
    pol = PriorityPolicy(level="low", min_failures_before_alert=3)
    assert should_alert(pol, "failure", consecutive_failures=2) is False


def test_should_alert_at_min_failures():
    pol = PriorityPolicy(level="low", min_failures_before_alert=3)
    assert should_alert(pol, "failure", consecutive_failures=3) is True


def test_should_alert_critical_always():
    pol = PriorityPolicy(level="critical")
    assert should_alert(pol, "miss") is True
    assert should_alert(pol, "failure", consecutive_failures=1) is True


# ---------------------------------------------------------------------------
# jobs_by_priority
# ---------------------------------------------------------------------------

def test_jobs_by_priority_sorted():
    jobs = [
        _FakeJob("low_job", {"level": "low"}),
        _FakeJob("critical_job", {"level": "critical"}),
        _FakeJob("medium_job", {"level": "medium"}),
    ]
    cfg = _FakeCfg(jobs)
    policies = parse_priority_policies(cfg)
    sorted_jobs = jobs_by_priority(jobs, policies)
    assert [j.name for j in sorted_jobs] == ["critical_job", "medium_job", "low_job"]


# ---------------------------------------------------------------------------
# parse_priority_policies
# ---------------------------------------------------------------------------

def test_parse_priority_policies_string_shorthand():
    jobs = [_FakeJob("j", "high")]
    cfg = _FakeCfg(jobs)
    policies = parse_priority_policies(cfg)
    assert policies["j"].level == "high"


def test_parse_priority_policies_no_priority_key():
    jobs = [_FakeJob("j")]
    cfg = _FakeCfg(jobs)
    policies = parse_priority_policies(cfg)
    assert policies["j"].level == DEFAULT_PRIORITY
