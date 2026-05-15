"""Tests for cronwatch.alerts_routing."""

import json
import os
import pytest

from cronwatch.config import AlertConfig, JobConfig
from cronwatch.alerts_routing import (
    RouteRule,
    RoutingConfig,
    load_routing_config,
    resolve_alert,
    _rule_matches,
)


def _make_job(name="backup", tags=None, labels=None):
    return JobConfig(
        name=name,
        command="echo hi",
        interval_seconds=3600,
        tags=tags or [],
        labels=labels or {},
    )


@pytest.fixture
def routing_file(tmp_path):
    data = {
        "routes": [
            {
                "match_job": "backup*",
                "alert": {"webhook_url": "http://backup-hook"},
            },
            {
                "match_tag": "critical",
                "alert": {"webhook_url": "http://critical-hook"},
            },
            {
                "match_label": "env=prod",
                "alert": {"webhook_url": "http://prod-hook"},
            },
        ],
        "default_alert": {"webhook_url": "http://default-hook"},
    }
    p = tmp_path / "routing.json"
    p.write_text(json.dumps(data))
    return str(p)


def test_load_routing_config_parses_routes(routing_file):
    cfg = load_routing_config(routing_file)
    assert len(cfg.routes) == 3
    assert cfg.routes[0].match_job == "backup*"
    assert cfg.routes[0].alert.webhook_url == "http://backup-hook"


def test_load_routing_config_default_alert(routing_file):
    cfg = load_routing_config(routing_file)
    assert cfg.default_alert is not None
    assert cfg.default_alert.webhook_url == "http://default-hook"


def test_load_routing_config_missing_file(tmp_path):
    cfg = load_routing_config(str(tmp_path / "nonexistent.json"))
    assert cfg.routes == []
    assert cfg.default_alert is None


def test_rule_matches_job_glob():
    rule = RouteRule(match_job="backup*", alert=AlertConfig())
    assert _rule_matches(rule, _make_job("backup_daily"))
    assert not _rule_matches(rule, _make_job("sync_files"))


def test_rule_matches_tag():
    rule = RouteRule(match_tag="critical", alert=AlertConfig())
    assert _rule_matches(rule, _make_job(tags=["critical", "db"]))
    assert not _rule_matches(rule, _make_job(tags=["db"]))


def test_rule_matches_label_key_value():
    rule = RouteRule(match_label="env=prod", alert=AlertConfig())
    assert _rule_matches(rule, _make_job(labels={"env": "prod"}))
    assert not _rule_matches(rule, _make_job(labels={"env": "staging"}))


def test_resolve_alert_first_match(routing_file):
    cfg = load_routing_config(routing_file)
    job = _make_job("backup_weekly")
    alert = resolve_alert(job, cfg)
    assert alert is not None
    assert alert.webhook_url == "http://backup-hook"


def test_resolve_alert_tag_match(routing_file):
    cfg = load_routing_config(routing_file)
    job = _make_job("sync", tags=["critical"])
    alert = resolve_alert(job, cfg)
    assert alert.webhook_url == "http://critical-hook"


def test_resolve_alert_falls_back_to_default(routing_file):
    cfg = load_routing_config(routing_file)
    job = _make_job("unmatched_job")
    alert = resolve_alert(job, cfg)
    assert alert.webhook_url == "http://default-hook"


def test_resolve_alert_no_default_returns_none():
    cfg = RoutingConfig(routes=[])
    job = _make_job("anything")
    assert resolve_alert(job, cfg) is None
