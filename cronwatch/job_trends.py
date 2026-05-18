"""Compute execution duration trends for cron jobs."""
from __future__ import annotations

import statistics
from dataclasses import dataclass, field
from pathlib import Path
from typing import List, Optional

from cronwatch.history import JobHistory


@dataclass
class TrendStats:
    job_name: str
    sample_count: int
    mean_duration: Optional[float]  # seconds
    median_duration: Optional[float]
    stdev_duration: Optional[float]
    min_duration: Optional[float]
    max_duration: Optional[float]
    trend: str  # "improving", "degrading", "stable", "unknown"

    def as_dict(self) -> dict:
        return {
            "job": self.job_name,
            "samples": self.sample_count,
            "mean_s": round(self.mean_duration, 3) if self.mean_duration is not None else None,
            "median_s": round(self.median_duration, 3) if self.median_duration is not None else None,
            "stdev_s": round(self.stdev_duration, 3) if self.stdev_duration is not None else None,
            "min_s": round(self.min_duration, 3) if self.min_duration is not None else None,
            "max_s": round(self.max_duration, 3) if self.max_duration is not None else None,
            "trend": self.trend,
        }

    def as_text(self) -> str:
        if self.mean_duration is None:
            return f"{self.job_name}: no duration data"
        return (
            f"{self.job_name}: mean={self.mean_duration:.1f}s "
            f"median={self.median_duration:.1f}s "
            f"stdev={self.stdev_duration:.1f}s "
            f"[{self.min_duration:.1f}s – {self.max_duration:.1f}s] "
            f"trend={self.trend}"
        )


def _detect_trend(durations: List[float], window: int = 5) -> str:
    """Compare the mean of the last *window* samples to the overall mean."""
    if len(durations) < window + 1:
        return "unknown"
    overall = statistics.mean(durations)
    recent = statistics.mean(durations[-window:])
    if overall == 0:
        return "stable"
    delta = (recent - overall) / overall
    if delta > 0.10:
        return "degrading"
    if delta < -0.10:
        return "improving"
    return "stable"


def compute_trend(job_name: str, history_dir: Path, limit: int = 50) -> TrendStats:
    """Return a TrendStats for *job_name* based on its execution history."""
    jh = JobHistory(job_name, history_dir)
    records = jh.records[-limit:]
    durations = [
        r.duration_seconds
        for r in records
        if r.duration_seconds is not None
    ]
    if not durations:
        return TrendStats(
            job_name=job_name,
            sample_count=len(records),
            mean_duration=None,
            median_duration=None,
            stdev_duration=None,
            min_duration=None,
            max_duration=None,
            trend="unknown",
        )
    stdev = statistics.stdev(durations) if len(durations) > 1 else 0.0
    return TrendStats(
        job_name=job_name,
        sample_count=len(durations),
        mean_duration=statistics.mean(durations),
        median_duration=statistics.median(durations),
        stdev_duration=stdev,
        min_duration=min(durations),
        max_duration=max(durations),
        trend=_detect_trend(durations),
    )


def compute_all_trends(config, history_dir: Path, limit: int = 50) -> List[TrendStats]:
    """Return TrendStats for every job in *config*."""
    return [compute_trend(job.name, history_dir, limit=limit) for job in config.jobs]
