"""Tests for cronwatch.job_templates."""

import pytest

from cronwatch.job_templates import (
    apply_template,
    delete_template,
    get_template,
    list_templates,
    set_template,
)


@pytest.fixture()
def state_dir(tmp_path):
    return str(tmp_path)


def test_get_template_missing_returns_none(state_dir):
    assert get_template(state_dir, "nope") is None


def test_set_template_returns_record(state_dir):
    rec = set_template(state_dir, "basic", {"interval": 3600, "grace": 60})
    assert rec["name"] == "basic"
    assert rec["defaults"]["interval"] == 3600


def test_set_template_persisted(state_dir):
    set_template(state_dir, "basic", {"interval": 3600})
    rec = get_template(state_dir, "basic")
    assert rec is not None
    assert rec["defaults"]["interval"] == 3600


def test_set_template_overwrites_existing(state_dir):
    set_template(state_dir, "basic", {"interval": 3600})
    set_template(state_dir, "basic", {"interval": 7200, "grace": 120})
    rec = get_template(state_dir, "basic")
    assert rec["defaults"]["interval"] == 7200
    assert rec["defaults"]["grace"] == 120


def test_delete_existing_returns_true(state_dir):
    set_template(state_dir, "basic", {"interval": 3600})
    assert delete_template(state_dir, "basic") is True
    assert get_template(state_dir, "basic") is None


def test_delete_missing_returns_false(state_dir):
    assert delete_template(state_dir, "ghost") is False


def test_list_templates_empty(state_dir):
    assert list_templates(state_dir) == []


def test_list_templates_sorted(state_dir):
    set_template(state_dir, "zebra", {"interval": 100})
    set_template(state_dir, "alpha", {"interval": 200})
    names = [r["name"] for r in list_templates(state_dir)]
    assert names == ["alpha", "zebra"]


def test_apply_template_merges_overrides(state_dir):
    set_template(state_dir, "base", {"interval": 3600, "grace": 60, "timeout": 300})
    result = apply_template(state_dir, "base", {"grace": 120})
    assert result["interval"] == 3600
    assert result["grace"] == 120
    assert result["timeout"] == 300


def test_apply_template_missing_raises(state_dir):
    with pytest.raises(KeyError, match="Template 'missing' not found"):
        apply_template(state_dir, "missing", {})


def test_apply_template_empty_overrides(state_dir):
    set_template(state_dir, "t", {"interval": 60})
    result = apply_template(state_dir, "t", {})
    assert result == {"interval": 60}
