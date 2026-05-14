"""Tests for cronwatch.retention_policy."""
from __future__ import annotations

import pytest
from unittest.mock import MagicMock

from cronwatch.retention_policy import (
    RetentionPolicy,
    _parse_policy,
    parse_retention_policies,
    effective_policy,
    _DEFAULT_POLICY,
)


def _make_job(name: str, retention: dict | None = None):
    j = MagicMock()
    j.name = name
    j.retention = retention
    return j


def _make_config(jobs, retention: dict | None = None):
    cfg = MagicMock()
    cfg.jobs = jobs
    cfg.retention = retention
    return cfg


# --- _parse_policy ---

def test_parse_policy_defaults():
    pol = _parse_policy({})
    assert pol.history_days == 30
    assert pol.state_days == 90
    assert pol.max_records is None


def test_parse_policy_full():
    pol = _parse_policy({"history_days": 7, "max_records": 100, "state_days": 14})
    assert pol.history_days == 7
    assert pol.max_records == 100
    assert pol.state_days == 14


def test_parse_policy_partial():
    pol = _parse_policy({"history_days": 60})
    assert pol.history_days == 60
    assert pol.state_days == 90  # default
    assert pol.max_records is None


# --- parse_retention_policies ---

def test_no_global_no_job_uses_defaults():
    cfg = _make_config([_make_job("backup")])
    policies = parse_retention_policies(cfg)
    pol = policies["backup"]
    assert pol.history_days == _DEFAULT_POLICY.history_days
    assert pol.state_days == _DEFAULT_POLICY.state_days


def test_global_policy_inherited_by_all_jobs():
    cfg = _make_config(
        [_make_job("a"), _make_job("b")],
        retention={"history_days": 14, "state_days": 60},
    )
    policies = parse_retention_policies(cfg)
    assert policies["a"].history_days == 14
    assert policies["b"].state_days == 60


def test_job_retention_overrides_global():
    cfg = _make_config(
        [_make_job("fast", retention={"history_days": 3, "max_records": 50})],
        retention={"history_days": 30},
    )
    policies = parse_retention_policies(cfg)
    pol = policies["fast"]
    assert pol.history_days == 3
    assert pol.max_records == 50
    # state_days should come from global (30 history but state default)
    assert pol.state_days == 90


def test_job_without_retention_uses_global():
    cfg = _make_config(
        [_make_job("nopolicy"), _make_job("withpolicy", retention={"history_days": 5})],
        retention={"history_days": 20},
    )
    policies = parse_retention_policies(cfg)
    assert policies["nopolicy"].history_days == 20
    assert policies["withpolicy"].history_days == 5


# --- effective_policy ---

def test_effective_policy_returns_known():
    pol = RetentionPolicy(history_days=7)
    policies = {"myjob": pol}
    assert effective_policy("myjob", policies) is pol


def test_effective_policy_falls_back_to_default():
    pol = effective_policy("unknown", {})
    assert pol is _DEFAULT_POLICY
