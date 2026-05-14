"""Tests for cronwatch.cli_metrics."""
import json
import pytest
from cronwatch.metrics import increment, reset_counter
from cronwatch.cli_metrics import main


@pytest.fixture()
def state_dir(tmp_path):
    return str(tmp_path)


def _run(state_dir, *args):
    return main(["--state-dir", state_dir, *args])


def test_show_no_metrics(state_dir, capsys):
    rc = _run(state_dir, "show")
    assert rc == 0
    out = capsys.readouterr().out
    assert "No metrics" in out


def test_show_with_counters(state_dir, capsys):
    increment(state_dir, "total.runs", 3)
    rc = _run(state_dir, "show")
    assert rc == 0
    out = capsys.readouterr().out
    assert "total.runs" in out
    assert "3" in out


def test_json_output(state_dir, capsys):
    increment(state_dir, "alerts.sent", 2)
    rc = _run(state_dir, "json")
    assert rc == 0
    data = json.loads(capsys.readouterr().out)
    assert data["alerts.sent"] == 2


def test_reset_specific_counter(state_dir, capsys):
    increment(state_dir, "x", 5)
    rc = _run(state_dir, "reset", "x")
    assert rc == 0
    from cronwatch.metrics import get_counter
    assert get_counter(state_dir, "x") == 0


def test_reset_all(state_dir, capsys):
    increment(state_dir, "a", 1)
    increment(state_dir, "b", 2)
    rc = _run(state_dir, "reset-all")
    assert rc == 0
    from cronwatch.metrics import get_counter
    assert get_counter(state_dir, "a") == 0
    assert get_counter(state_dir, "b") == 0
    out = capsys.readouterr().out
    assert "2 counter" in out


def test_no_command_returns_1(state_dir):
    rc = _run(state_dir)
    assert rc == 1
