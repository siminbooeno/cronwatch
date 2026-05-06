"""Digest report generation for cronwatch — summarises job health across all tracked jobs."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from typing import List, Optional

from cronwatch.config import CronwatchConfig
from cronwatch.history import JobHistory
from cronwatch.state import last_seen_dt


@dataclass
class JobSummary:
    name: str
    last_seen: Optional[datetime]
    success_rate: float  # 0.0 – 1.0
    consecutive_failures: int
    total_runs: int


@dataclass
class DigestReport:
    generated_at: datetime
    jobs: List[JobSummary]

    @property
    def healthy_count(self) -> int:
        return sum(1 for j in self.jobs if j.consecutive_failures == 0)

    @property
    def unhealthy_count(self) -> int:
        return len(self.jobs) - self.healthy_count

    def as_text(self) -> str:
        lines = [
            f"CronWatch Digest — {self.generated_at.strftime('%Y-%m-%d %H:%M UTC')}",
            f"Jobs: {len(self.jobs)} total, {self.healthy_count} healthy, {self.unhealthy_count} unhealthy",
            "-" * 60,
        ]
        for job in self.jobs:
            seen = job.last_seen.strftime("%Y-%m-%d %H:%M UTC") if job.last_seen else "never"
            status = "OK" if job.consecutive_failures == 0 else f"FAIL x{job.consecutive_failures}"
            lines.append(
                f"  {job.name:<30} {status:<12} "
                f"rate={job.success_rate:.0%}  runs={job.total_runs}  last={seen}"
            )
        return "\n".join(lines)


def build_digest(config: CronwatchConfig, history_dir: str, state_dir: str) -> DigestReport:
    """Build a DigestReport for all jobs defined in *config*."""
    summaries: List[JobSummary] = []

    for job in config.jobs:
        history = JobHistory(history_dir, job.name)
        records = history.all()

        total = len(records)
        successes = sum(1 for r in records if r.success)
        rate = successes / total if total else 0.0

        consec = 0
        for r in reversed(records):
            if not r.success:
                consec += 1
            else:
                break

        last_seen = last_seen_dt(state_dir, job.name)

        summaries.append(
            JobSummary(
                name=job.name,
                last_seen=last_seen,
                success_rate=rate,
                consecutive_failures=consec,
                total_runs=total,
            )
        )

    return DigestReport(generated_at=datetime.now(timezone.utc), jobs=summaries)
