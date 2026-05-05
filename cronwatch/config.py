"""Configuration loader for cronwatch."""

import os
import json
from dataclasses import dataclass, field
from typing import List, Optional


@dataclass
class JobConfig:
    name: str
    schedule: str  # cron expression
    grace_period: int = 60  # seconds after expected run before alerting
    timeout: Optional[int] = None  # max allowed runtime in seconds


@dataclass
class AlertConfig:
    webhook_url: Optional[str] = None
    email_to: Optional[str] = None
    email_from: Optional[str] = None
    smtp_host: str = "localhost"
    smtp_port: int = 25


@dataclass
class CronwatchConfig:
    jobs: List[JobConfig] = field(default_factory=list)
    alert: AlertConfig = field(default_factory=AlertConfig)
    check_interval: int = 30  # seconds between checks
    state_file: str = ".cronwatch_state.json"


def load_config(path: str = "cronwatch.json") -> CronwatchConfig:
    """Load configuration from a JSON file."""
    if not os.path.exists(path):
        raise FileNotFoundError(f"Config file not found: {path}")

    with open(path, "r") as f:
        data = json.load(f)

    jobs = [
        JobConfig(
            name=j["name"],
            schedule=j["schedule"],
            grace_period=j.get("grace_period", 60),
            timeout=j.get("timeout"),
        )
        for j in data.get("jobs", [])
    ]

    alert_data = data.get("alert", {})
    alert = AlertConfig(
        webhook_url=alert_data.get("webhook_url"),
        email_to=alert_data.get("email_to"),
        email_from=alert_data.get("email_from"),
        smtp_host=alert_data.get("smtp_host", "localhost"),
        smtp_port=alert_data.get("smtp_port", 25),
    )

    return CronwatchConfig(
        jobs=jobs,
        alert=alert,
        check_interval=data.get("check_interval", 30),
        state_file=data.get("state_file", ".cronwatch_state.json"),
    )
