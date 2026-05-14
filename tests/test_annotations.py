"""Tests for cronwatch.annotations and cronwatch.cli_annotations."""
from __future__ import annotations

import json
from pathlib import Path

import pytest

from cronwatch.annotations import (
    add_annotation,
    delete_annotations,
    get_annotations,
)
from cronwatch.cli_annotations import _build_parser, cmd_add, cmd_delete, cmd_list


@pytest.fixture()
def state_dir(tmp_path: Path) -> str:
    return str(tmp_path)


# ---------------------------------------------------------------------------
# annotations module
# ---------------------------------------------------------------------------

def test_get_annotations_empty(state_dir):
    assert get_annotations(state_dir, "backup") == []


def test_add_annotation_returns_record(state_dir):
    r = add_annotation(state_dir, "backup", "owner", "alice")
    assert r["key"] == "owner"
    assert r["value"] == "alice"
    assert "ts" in r


def test_add_annotation_with_author(state_dir):
    r = add_annotation(state_dir, "backup", "note", "ok", author="bob")
    assert r["author"] == "bob"


def test_add_annotation_persisted(state_dir):
    add_annotation(state_dir, "sync", "env", "prod")
    records = get_annotations(state_dir, "sync")
    assert len(records) == 1
    assert records[0]["value"] == "prod"


def test_get_annotations_filter_by_key(state_dir):
    add_annotation(state_dir, "job", "env", "prod")
    add_annotation(state_dir, "job", "owner", "alice")
    result = get_annotations(state_dir, "job", key="env")
    assert len(result) == 1
    assert result[0]["key"] == "env"


def test_multiple_annotations_accumulated(state_dir):
    for i in range(3):
        add_annotation(state_dir, "job", "run", str(i))
    assert len(get_annotations(state_dir, "job")) == 3


def test_delete_all_annotations(state_dir):
    add_annotation(state_dir, "job", "a", "1")
    add_annotation(state_dir, "job", "b", "2")
    removed = delete_annotations(state_dir, "job")
    assert removed == 2
    assert get_annotations(state_dir, "job") == []


def test_delete_by_key(state_dir):
    add_annotation(state_dir, "job", "env", "prod")
    add_annotation(state_dir, "job", "owner", "alice")
    removed = delete_annotations(state_dir, "job", key="env")
    assert removed == 1
    remaining = get_annotations(state_dir, "job")
    assert len(remaining) == 1
    assert remaining[0]["key"] == "owner"


def test_delete_nonexistent_returns_zero(state_dir):
    assert delete_annotations(state_dir, "ghost", key="x") == 0


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def _ns(state_dir, **kwargs):
    import argparse
    ns = argparse.Namespace(state_dir=state_dir, **kwargs)
    return ns


def test_cmd_add_prints_confirmation(state_dir, capsys):
    args = _ns(state_dir, job="myjob", key="env", value="staging", author=None)
    rc = cmd_add(args)
    assert rc == 0
    out = capsys.readouterr().out
    assert "env=staging" in out


def test_cmd_list_no_annotations(state_dir, capsys):
    args = _ns(state_dir, job="empty", key=None, as_json=False)
    rc = cmd_list(args)
    assert rc == 0
    assert "No annotations" in capsys.readouterr().out


def test_cmd_list_json(state_dir, capsys):
    add_annotation(state_dir, "job", "k", "v")
    args = _ns(state_dir, job="job", key=None, as_json=True)
    cmd_list(args)
    data = json.loads(capsys.readouterr().out)
    assert isinstance(data, list)
    assert data[0]["key"] == "k"


def test_cmd_delete_reports_count(state_dir, capsys):
    add_annotation(state_dir, "job", "x", "1")
    add_annotation(state_dir, "job", "x", "2")
    args = _ns(state_dir, job="job", key="x")
    rc = cmd_delete(args)
    assert rc == 0
    assert "2" in capsys.readouterr().out
