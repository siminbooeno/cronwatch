"""Configuration loading for cronwatch."""
from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional


@dataclass
class JobConfig:
    name: str
    command: str
    interval_seconds: int
    grace_seconds: int = 60
    timeout_seconds: Optional[int] = None
    tags: List[str] = field(default_factory=list)
    labels: Dict[str, str] = field(default_factory=dict)


@dataclass
class AlertConfig:
    webhook_url: Optional[str]
    email_to: Optional[str]
    email_from: Optional[str]
    smtp_host: Optional[str]
    smtp_port: int = 25


@dataclass
class CronwatchConfig:
    jobs: List[JobConfig]
    alert: AlertConfig
    state_dir: str
    history_dir: str


def _parse_job(raw: Dict[str, Any]) -> JobConfig:
    return JobConfig(
        name=raw["name"],
        command=raw["command"],
        interval_seconds=int(raw["interval_seconds"]),
        grace_seconds=int(raw.get("grace_seconds", 60)),
        timeout_seconds=raw.get("timeout_seconds"),
        tags=raw.get("tags", []),
        labels={str(k): str(v) for k, v in raw.get("labels", {}).items()},
    )


def load_config(path: str) -> CronwatchConfig:
    data = json.loads(Path(path).read_text())
    raw_alert = data.get("alert", {})
    alert = AlertConfig(
        webhook_url=raw_alert.get("webhook_url"),
        email_to=raw_alert.get("email_to"),
        email_from=raw_alert.get("email_from"),
        smtp_host=raw_alert.get("smtp_host"),
        smtp_port=int(raw_alert.get("smtp_port", 25)),
    )
    jobs = [_parse_job(j) for j in data.get("jobs", [])]
    return CronwatchConfig(
        jobs=jobs,
        alert=alert,
        state_dir=data.get("state_dir", "/var/lib/cronwatch/state"),
        history_dir=data.get("history_dir", "/var/lib/cronwatch/history"),
    )
