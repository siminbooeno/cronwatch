"""Configuration loading for cronwatch."""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional


@dataclass
class JobConfig:
    name: str
    command: str
    interval_seconds: Optional[int] = None
    grace_seconds: Optional[int] = None
    timeout_seconds: Optional[int] = None
    tags: List[str] = field(default_factory=list)
    labels: Dict[str, str] = field(default_factory=dict)
    depends_on: List[str] = field(default_factory=list)


@dataclass
class AlertConfig:
    webhook_url: Optional[str] = None
    email_to: Optional[str] = None
    email_from: Optional[str] = None
    smtp_host: Optional[str] = None
    smtp_port: int = 25
    cooldown_seconds: int = 3600


@dataclass
class CronwatchConfig:
    jobs: List[JobConfig]
    alert: AlertConfig
    state_dir: str = "/var/lib/cronwatch"
    history_dir: Optional[str] = None
    report_interval_seconds: Optional[int] = None


def _parse_job(raw: Dict[str, Any]) -> JobConfig:
    return JobConfig(
        name=raw["name"],
        command=raw["command"],
        interval_seconds=raw.get("interval_seconds"),
        grace_seconds=raw.get("grace_seconds"),
        timeout_seconds=raw.get("timeout_seconds"),
        tags=raw.get("tags", []),
        labels=raw.get("labels", {}),
        depends_on=raw.get("depends_on", []),
    )


def load_config(path: str) -> CronwatchConfig:
    with open(path) as fh:
        data = json.load(fh)

    alert_raw = data.get("alert", {})
    alert = AlertConfig(
        webhook_url=alert_raw.get("webhook_url"),
        email_to=alert_raw.get("email_to"),
        email_from=alert_raw.get("email_from"),
        smtp_host=alert_raw.get("smtp_host"),
        smtp_port=alert_raw.get("smtp_port", 25),
        cooldown_seconds=alert_raw.get("cooldown_seconds", 3600),
    )

    jobs = [_parse_job(j) for j in data.get("jobs", [])]

    return CronwatchConfig(
        jobs=jobs,
        alert=alert,
        state_dir=data.get("state_dir", "/var/lib/cronwatch"),
        history_dir=data.get("history_dir"),
        report_interval_seconds=data.get("report_interval_seconds"),
    )
