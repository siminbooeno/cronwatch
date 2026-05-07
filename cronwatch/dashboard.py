"""Simple text-based status dashboard for cronwatch jobs."""

from __future__ import annotations

import datetime
from dataclasses import dataclass
from typing import List, Optional

from cronwatch.config import CronwatchConfig
from cronwatch.history import JobHistory
from cronwatch.state import last_seen_dt


@dataclass
class JobRow:
    name: str
    last_seen: Optional[str]
    status: str  # OK | MISSING | FAILING
    success_rate: float
    consecutive_failures: int


def _status_label(consecutive_failures: int, last_seen: Optional[datetime.datetime]) -> str:
    if last_seen is None:
        return "MISSING"
    if consecutive_failures > 0:
        return "FAILING"
    return "OK"


def build_dashboard(cfg: CronwatchConfig, state_dir: str, history_dir: str) -> List[JobRow]:
    """Return a list of JobRow summaries for all configured jobs."""
    rows: List[JobRow] = []
    for job in cfg.jobs:
        history = JobHistory(history_dir, job.name)
        dt = last_seen_dt(state_dir, job.name)
        last_seen_str = dt.strftime("%Y-%m-%d %H:%M:%S UTC") if dt else "never"
        rate = history.success_rate()
        cf = history.consecutive_failures()
        status = _status_label(cf, dt)
        rows.append(
            JobRow(
                name=job.name,
                last_seen=last_seen_str,
                status=status,
                success_rate=rate,
                consecutive_failures=cf,
            )
        )
    return rows


def render_text(rows: List[JobRow]) -> str:
    """Render dashboard rows as a plain-text table."""
    if not rows:
        return "No jobs configured.\n"

    col_widths = {
        "name": max(len(r.name) for r in rows),
        "last_seen": 23,
        "status": 7,
        "rate": 8,
        "cf": 4,
    }
    col_widths["name"] = max(col_widths["name"], 4)

    header = (
        f"{'JOB':<{col_widths['name']}}  "
        f"{'LAST SEEN':<{col_widths['last_seen']}}  "
        f"{'STATUS':<{col_widths['status']}}  "
        f"{'RATE':>{col_widths['rate']}}  "
        f"{'CF':>{col_widths['cf']}}"
    )
    sep = "-" * len(header)
    lines = [header, sep]
    for r in rows:
        rate_str = f"{r.success_rate * 100:.1f}%"
        lines.append(
            f"{r.name:<{col_widths['name']}}  "
            f"{r.last_seen:<{col_widths['last_seen']}}  "
            f"{r.status:<{col_widths['status']}}  "
            f"{rate_str:>{col_widths['rate']}}  "
            f"{r.consecutive_failures:>{col_widths['cf']}}"
        )
    lines.append("")
    return "\n".join(lines)
