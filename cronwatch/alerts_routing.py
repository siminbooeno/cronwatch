"""Alert routing: direct alerts to the right recipients based on job tags, labels, or name patterns."""

from __future__ import annotations

import fnmatch
import json
import os
from dataclasses import dataclass, field
from typing import List, Optional

from cronwatch.config import AlertConfig, JobConfig


@dataclass
class RouteRule:
    """A single routing rule mapping a selector to an alert target."""
    match_job: Optional[str] = None        # glob pattern for job name
    match_tag: Optional[str] = None        # tag that must be present
    match_label: Optional[str] = None      # key=value label selector
    alert: AlertConfig = field(default_factory=AlertConfig)


@dataclass
class RoutingConfig:
    routes: List[RouteRule] = field(default_factory=list)
    default_alert: Optional[AlertConfig] = None


def _parse_route(raw: dict) -> RouteRule:
    alert_raw = raw.get("alert", {})
    alert = AlertConfig(
        webhook_url=alert_raw.get("webhook_url"),
        email_to=alert_raw.get("email_to"),
        email_from=alert_raw.get("email_from"),
        smtp_host=alert_raw.get("smtp_host", "localhost"),
        smtp_port=int(alert_raw.get("smtp_port", 25)),
    )
    return RouteRule(
        match_job=raw.get("match_job"),
        match_tag=raw.get("match_tag"),
        match_label=raw.get("match_label"),
        alert=alert,
    )


def load_routing_config(path: str) -> RoutingConfig:
    """Load routing rules from a JSON file."""
    if not os.path.exists(path):
        return RoutingConfig()
    with open(path) as fh:
        raw = json.load(fh)
    routes = [_parse_route(r) for r in raw.get("routes", [])]
    default_raw = raw.get("default_alert")
    default_alert = None
    if default_raw:
        default_alert = AlertConfig(
            webhook_url=default_raw.get("webhook_url"),
            email_to=default_raw.get("email_to"),
            email_from=default_raw.get("email_from"),
            smtp_host=default_raw.get("smtp_host", "localhost"),
            smtp_port=int(default_raw.get("smtp_port", 25)),
        )
    return RoutingConfig(routes=routes, default_alert=default_alert)


def _rule_matches(rule: RouteRule, job: JobConfig) -> bool:
    if rule.match_job and not fnmatch.fnmatch(job.name, rule.match_job):
        return False
    if rule.match_tag:
        tags = getattr(job, "tags", []) or []
        if rule.match_tag not in tags:
            return False
    if rule.match_label:
        labels = getattr(job, "labels", {}) or {}
        if "=" in rule.match_label:
            k, v = rule.match_label.split("=", 1)
            if labels.get(k) != v:
                return False
        else:
            if rule.match_label not in labels:
                return False
    return True


def resolve_alert(job: JobConfig, routing: RoutingConfig) -> Optional[AlertConfig]:
    """Return the first matching AlertConfig for a job, or the default."""
    for rule in routing.routes:
        if _rule_matches(rule, job):
            return rule.alert
    return routing.default_alert
