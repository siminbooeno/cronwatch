"""Configuration loading for cronwatch.

Extends the original config with an optional ``tags`` field on JobConfig.
"""
from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any


@dataclass
class JobConfig:
    name: str
    command: str
    interval_seconds: int
    grace_seconds: int = 60
    timeout_seconds: int | None = None
    tags: list[str] = field(default_factory=list)


@dataclass
class AlertConfig:
    webhook_url: str | None = None
    email_to: str | None = None
    email_from: str | None = None
    smtp_host: str = "localhost"
    smtp_port: int = 25


@dataclass
class CronwatchConfig:
    jobs: list[JobConfig]
    alert: AlertConfig
    state_dir: str = "/tmp/cronwatch/state"
    history_dir: str = "/tmp/cronwatch/history"
    history_retention_days: int = 30
    check_interval_seconds: int = 60
    digest_interval_seconds: int = 86400


def _parse_job(raw: dict[str, Any]) -> JobConfig:
    return JobConfig(
        name=raw["name"],
        command=raw["command"],
        interval_seconds=int(raw["interval_seconds"]),
        grace_seconds=int(raw.get("grace_seconds", 60)),
        timeout_seconds=raw.get("timeout_seconds"),
        tags=list(raw.get("tags", [])),
    )


def load_config(path: str | Path) -> CronwatchConfig:
    data = json.loads(Path(path).read_text())

    alert_raw = data.get("alert", {})
    alert = AlertConfig(
        webhook_url=alert_raw.get("webhook_url"),
        email_to=alert_raw.get("email_to"),
        email_from=alert_raw.get("email_from"),
        smtp_host=alert_raw.get("smtp_host", "localhost"),
        smtp_port=int(alert_raw.get("smtp_port", 25)),
    )

    return CronwatchConfig(
        jobs=[_parse_job(j) for j in data.get("jobs", [])],
        alert=alert,
        state_dir=data.get("state_dir", "/tmp/cronwatch/state"),
        history_dir=data.get("history_dir", "/tmp/cronwatch/history"),
        history_retention_days=int(data.get("history_retention_days", 30)),
        check_interval_seconds=int(data.get("check_interval_seconds", 60)),
        digest_interval_seconds=int(data.get("digest_interval_seconds", 86400)),
    )
