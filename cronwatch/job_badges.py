"""Job status badges — generate shield-style badge data for jobs."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

from cronwatch.history import JobHistory
from cronwatch.pauses import is_paused


@dataclass
class Badge:
    job_name: str
    label: str
    message: str
    color: str

    def as_dict(self) -> dict:
        return {
            "schemaVersion": 1,
            "label": self.label,
            "message": self.message,
            "color": self.color,
        }

    def as_text(self) -> str:
        return f"{self.label}: {self.message} [{self.color}]"


_COLOR_SUCCESS = "brightgreen"
_COLOR_FAILURE = "red"
_COLOR_PAUSED = "yellow"
_COLOR_UNKNOWN = "lightgrey"


def _success_rate_color(rate: float) -> str:
    if rate >= 0.95:
        return _COLOR_SUCCESS
    if rate >= 0.80:
        return "orange"
    return _COLOR_FAILURE


def build_badge(
    job_name: str,
    history_dir: str,
    state_dir: str,
    label: Optional[str] = None,
    window: int = 30,
) -> Badge:
    """Build a Badge for *job_name* based on recent execution history."""
    effective_label = label or job_name

    if is_paused(job_name, state_dir=state_dir):
        return Badge(
            job_name=job_name,
            label=effective_label,
            message="paused",
            color=_COLOR_PAUSED,
        )

    history = JobHistory(job_name, history_dir=history_dir)
    records = history.records()

    if not records:
        return Badge(
            job_name=job_name,
            label=effective_label,
            message="unknown",
            color=_COLOR_UNKNOWN,
        )

    recent = records[-window:]
    rate = history.success_rate(window=window)
    successes = sum(1 for r in recent if r.success)
    total = len(recent)
    message = f"{successes}/{total} passing"
    color = _success_rate_color(rate)

    return Badge(
        job_name=job_name,
        label=effective_label,
        message=message,
        color=color,
    )
