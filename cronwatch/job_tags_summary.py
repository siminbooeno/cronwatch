"""Aggregate job status summaries grouped by tag."""
from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List

from cronwatch.config import CronwatchConfig
from cronwatch.history import JobHistory
from cronwatch.tags import all_tags, jobs_with_tag


@dataclass
class TagSummary:
    tag: str
    total_jobs: int = 0
    healthy_jobs: int = 0
    failing_jobs: int = 0
    never_run_jobs: int = 0
    avg_success_rate: float = 1.0
    job_names: List[str] = field(default_factory=list)

    def as_dict(self) -> dict:
        return {
            "tag": self.tag,
            "total_jobs": self.total_jobs,
            "healthy_jobs": self.healthy_jobs,
            "failing_jobs": self.failing_jobs,
            "never_run_jobs": self.never_run_jobs,
            "avg_success_rate": round(self.avg_success_rate, 4),
            "job_names": self.job_names,
        }

    def as_text(self) -> str:
        return (
            f"[{self.tag}] jobs={self.total_jobs} "
            f"healthy={self.healthy_jobs} "
            f"failing={self.failing_jobs} "
            f"never_run={self.never_run_jobs} "
            f"avg_success_rate={self.avg_success_rate:.1%}"
        )


def build_tag_summaries(
    cfg: CronwatchConfig,
    history_dir: str | Path,
) -> Dict[str, TagSummary]:
    """Return a TagSummary for every tag present in the config."""
    history_dir = Path(history_dir)
    summaries: Dict[str, TagSummary] = {}

    for tag in all_tags(cfg):
        tagged_jobs = jobs_with_tag(cfg, tag)
        summary = TagSummary(tag=tag, total_jobs=len(tagged_jobs))
        rates: List[float] = []

        for job in tagged_jobs:
            summary.job_names.append(job.name)
            hist = JobHistory(job.name, history_dir)
            records = hist.records()
            if not records:
                summary.never_run_jobs += 1
                continue
            rate = hist.success_rate()
            rates.append(rate)
            cf = hist.consecutive_failures()
            if cf > 0:
                summary.failing_jobs += 1
            else:
                summary.healthy_jobs += 1

        summary.avg_success_rate = (
            sum(rates) / len(rates) if rates else 1.0
        )
        summaries[tag] = summary

    return summaries
