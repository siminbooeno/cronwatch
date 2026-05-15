"""Tests for cronwatch.job_weights."""

from __future__ import annotations

import json
import os
import pytest

from cronwatch.job_weights import (
    DEFAULT_WEIGHT,
    WeightPolicy,
    get_weight,
    load_weight_policies,
    parse_weight_policies,
    rank_jobs,
)


# ---------------------------------------------------------------------------
# parse_weight_policies
# ---------------------------------------------------------------------------

def test_parse_weight_policies_empty():
    assert parse_weight_policies([]) == []


def test_parse_weight_policies_single():
    raw = [{"job": "backup", "weight": 5.0, "reason": "critical"}]
    result = parse_weight_policies(raw)
    assert len(result) == 1
    assert result[0].job_name == "backup"
    assert result[0].weight == 5.0
    assert result[0].reason == "critical"


def test_parse_weight_policies_defaults_weight():
    raw = [{"job": "cleanup"}]
    result = parse_weight_policies(raw)
    assert result[0].weight == DEFAULT_WEIGHT
    assert result[0].reason is None


# ---------------------------------------------------------------------------
# get_weight
# ---------------------------------------------------------------------------

def _policies() -> list[WeightPolicy]:
    return [
        WeightPolicy(job_name="high", weight=10.0),
        WeightPolicy(job_name="low", weight=0.5),
    ]


def test_get_weight_known_job():
    assert get_weight("high", _policies()) == 10.0


def test_get_weight_unknown_job_returns_default():
    assert get_weight("unknown", _policies()) == DEFAULT_WEIGHT


def test_get_weight_low_job():
    assert get_weight("low", _policies()) == 0.5


# ---------------------------------------------------------------------------
# rank_jobs
# ---------------------------------------------------------------------------

def test_rank_jobs_sorted_descending():
    ranked = rank_jobs(["low", "high", "unknown"], _policies())
    assert ranked[0] == "high"
    assert ranked[-1] == "low"


def test_rank_jobs_unknown_gets_default_position():
    ranked = rank_jobs(["low", "unknown"], _policies())
    # unknown has weight 1.0, low has weight 0.5 → unknown before low
    assert ranked[0] == "unknown"
    assert ranked[1] == "low"


# ---------------------------------------------------------------------------
# load_weight_policies
# ---------------------------------------------------------------------------

def test_load_weight_policies_missing_file(tmp_path):
    result = load_weight_policies(str(tmp_path / "nope.json"))
    assert result == []


def test_load_weight_policies_reads_file(tmp_path):
    data = {"weights": [{"job": "etl", "weight": 3.0, "reason": "revenue"}]}
    p = tmp_path / "weights.json"
    p.write_text(json.dumps(data))
    result = load_weight_policies(str(p))
    assert len(result) == 1
    assert result[0].job_name == "etl"
    assert result[0].weight == 3.0


def test_load_weight_policies_empty_weights_key(tmp_path):
    p = tmp_path / "weights.json"
    p.write_text(json.dumps({"weights": []}))
    assert load_weight_policies(str(p)) == []
