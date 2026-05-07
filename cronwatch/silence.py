"""Silence windows: suppress alerts for specific jobs during defined time ranges."""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from datetime import datetime, timezone, time
from typing import List, Optional


@dataclass
class SilenceWindow:
    """A time window during which alerts for a job are suppressed."""

    job_name: str
    start: time  # UTC
    end: time    # UTC
    days: List[int] = field(default_factory=lambda: list(range(7)))  # 0=Mon … 6=Sun
    reason: str = ""


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


def _parse_time(value: str) -> time:
    """Parse HH:MM string into a time object."""
    match = re.fullmatch(r"(\d{1,2}):(\d{2})", value.strip())
    if not match:
        raise ValueError(f"Invalid time format: {value!r}. Expected HH:MM.")
    return time(int(match.group(1)), int(match.group(2)))


def parse_silence_window(raw: dict) -> SilenceWindow:
    """Build a SilenceWindow from a config dict entry."""
    return SilenceWindow(
        job_name=raw["job"],
        start=_parse_time(raw["start"]),
        end=_parse_time(raw["end"]),
        days=raw.get("days", list(range(7))),
        reason=raw.get("reason", ""),
    )


def is_silenced(
    job_name: str,
    windows: List[SilenceWindow],
    now: Optional[datetime] = None,
) -> bool:
    """Return True if *job_name* is currently inside any matching silence window."""
    if not windows:
        return False
    now = now or _utcnow()
    current_time = now.time().replace(tzinfo=None)
    current_day = now.weekday()  # 0=Monday

    for w in windows:
        if w.job_name != job_name:
            continue
        if current_day not in w.days:
            continue
        # Handle windows that wrap midnight (e.g. 23:00 – 01:00)
        if w.start <= w.end:
            if w.start <= current_time <= w.end:
                return True
        else:
            if current_time >= w.start or current_time <= w.end:
                return True
    return False


def active_windows(
    job_name: str, windows: List[SilenceWindow]
) -> List[SilenceWindow]:
    """Return all silence windows defined for *job_name*."""
    return [w for w in windows if w.job_name == job_name]
