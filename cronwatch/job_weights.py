"""Job weight/importance scoring for prioritised alerting and reporting."""

from __future__ import annotations

import json
import os
from dataclasses import dataclass
from typing import Any, Dict, List, Optional

DEFAULT_WEIGHT = 1.0


@dataclass
class WeightPolicy:
    job_name: str
    weight: float
    reason: Optional[str] = None


def _parse_weight(raw: Dict[str, Any]) -> WeightPolicy:
    return WeightPolicy(
        job_name=raw["job"],
        weight=float(raw.get("weight", DEFAULT_WEIGHT)),
        reason=raw.get("reason"),
    )


def parse_weight_policies(raw_list: List[Dict[str, Any]]) -> List[WeightPolicy]:
    """Parse a list of raw weight policy dicts into WeightPolicy objects."""
    return [_parse_weight(r) for r in raw_list]


def get_weight(job_name: str, policies: List[WeightPolicy]) -> float:
    """Return the configured weight for *job_name*, or DEFAULT_WEIGHT if not found."""
    for p in policies:
        if p.job_name == job_name:
            return p.weight
    return DEFAULT_WEIGHT


def rank_jobs(job_names: List[str], policies: List[WeightPolicy]) -> List[str]:
    """Return *job_names* sorted by descending weight (heaviest first)."""
    return sorted(job_names, key=lambda j: get_weight(j, policies), reverse=True)


def load_weight_policies(config_path: str) -> List[WeightPolicy]:
    """Load weight policies from a JSON file.  Returns [] if file is absent."""
    if not os.path.exists(config_path):
        return []
    with open(config_path) as fh:
        data = json.load(fh)
    return parse_weight_policies(data.get("weights", []))
