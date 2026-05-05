"""Tests for cronwatch configuration loader."""

import json
import os
import pytest
import tempfile

from cronwatch.config import load_config, CronwatchConfig, JobConfig, AlertConfig


@pytest.fixture
def sample_config_file():
    config = {
        "check_interval": 60,
        "state_file": "/tmp/test_state.json",
        "alert": {
            "webhook_url": "https://hooks.test.com/webhook",
            "email_to": "test@example.com",
            "smtp_host": "smtp.test.com",
            "smtp_port": 587,
        },
        "jobs": [
            {"name": "job-a", "schedule": "0 * * * *", "grace_period": 90},
            {"name": "job-b", "schedule": "*/5 * * * *", "timeout": 120},
        ],
    }
    with tempfile.NamedTemporaryFile(
        mode="w", suffix=".json", delete=False
    ) as f:
        json.dump(config, f)
        yield f.name
    os.unlink(f.name)


def test_load_config_returns_cronwatch_config(sample_config_file):
    config = load_config(sample_config_file)
    assert isinstance(config, CronwatchConfig)


def test_load_config_jobs(sample_config_file):
    config = load_config(sample_config_file)
    assert len(config.jobs) == 2
    assert isinstance(config.jobs[0], JobConfig)
    assert config.jobs[0].name == "job-a"
    assert config.jobs[0].schedule == "0 * * * *"
    assert config.jobs[0].grace_period == 90
    assert config.jobs[0].timeout is None


def test_load_config_job_with_timeout(sample_config_file):
    config = load_config(sample_config_file)
    assert config.jobs[1].timeout == 120
    assert config.jobs[1].grace_period == 60  # default


def test_load_config_alert(sample_config_file):
    config = load_config(sample_config_file)
    assert isinstance(config.alert, AlertConfig)
    assert config.alert.webhook_url == "https://hooks.test.com/webhook"
    assert config.alert.email_to == "test@example.com"
    assert config.alert.smtp_port == 587


def test_load_config_top_level_fields(sample_config_file):
    config = load_config(sample_config_file)
    assert config.check_interval == 60
    assert config.state_file == "/tmp/test_state.json"


def test_load_config_file_not_found():
    with pytest.raises(FileNotFoundError):
        load_config("/nonexistent/path/config.json")


def test_load_config_defaults():
    minimal = {"jobs": [{"name": "j", "schedule": "* * * * *"}]}
    with tempfile.NamedTemporaryFile(
        mode="w", suffix=".json", delete=False
    ) as f:
        json.dump(minimal, f)
        path = f.name
    try:
        config = load_config(path)
        assert config.check_interval == 30
        assert config.state_file == ".cronwatch_state.json"
        assert config.alert.smtp_host == "localhost"
    finally:
        os.unlink(path)
