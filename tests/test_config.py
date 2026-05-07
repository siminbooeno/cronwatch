"""Tests for cronwatch.config loading."""
from __future__ import annotations

import json
import pathlib

import pytest

from cronwatch.config import CronwatchConfig, load_config


@pytest.fixture()
def sample_config_file(tmp_path: pathlib.Path) -> pathlib.Path:
    cfg = {
        "state_dir": str(tmp_path / "state"),
        "history_dir": str(tmp_path / "history"),
        "alert": {
            "webhook_url": "https://hooks.example.com/test",
            "email_to": "ops@example.com",
        },
        "jobs": [
            {
                "name": "job-a",
                "command": "echo a",
                "interval_seconds": 3600,
            },
            {
                "name": "job-b",
                "command": "echo b",
                "interval_seconds": 86400,
                "grace_seconds": 300,
                "timeout_seconds": 600,
                "tags": ["backup", "critical"],
            },
        ],
    }
    p = tmp_path / "config.json"
    p.write_text(json.dumps(cfg))
    return p


def test_load_config_returns_cronwatch_config(sample_config_file: pathlib.Path) -> None:
    cfg = load_config(sample_config_file)
    assert isinstance(cfg, CronwatchConfig)


def test_load_config_jobs(sample_config_file: pathlib.Path) -> None:
    cfg = load_config(sample_config_file)
    assert len(cfg.jobs) == 2
    assert cfg.jobs[0].name == "job-a"
    assert cfg.jobs[1].name == "job-b"


def test_load_config_job_with_timeout(sample_config_file: pathlib.Path) -> None:
    cfg = load_config(sample_config_file)
    assert cfg.jobs[1].timeout_seconds == 600


def test_load_config_alert(sample_config_file: pathlib.Path) -> None:
    cfg = load_config(sample_config_file)
    assert cfg.alert.webhook_url == "https://hooks.example.com/test"
    assert cfg.alert.email_to == "ops@example.com"


def test_load_config_default_grace(sample_config_file: pathlib.Path) -> None:
    cfg = load_config(sample_config_file)
    assert cfg.jobs[0].grace_seconds == 60


def test_load_config_tags_parsed(sample_config_file: pathlib.Path) -> None:
    cfg = load_config(sample_config_file)
    assert cfg.jobs[1].tags == ["backup", "critical"]


def test_load_config_tags_default_empty(sample_config_file: pathlib.Path) -> None:
    cfg = load_config(sample_config_file)
    assert cfg.jobs[0].tags == []


def test_load_config_state_dir(sample_config_file: pathlib.Path, tmp_path: pathlib.Path) -> None:
    cfg = load_config(sample_config_file)
    assert cfg.state_dir == str(tmp_path / "state")
