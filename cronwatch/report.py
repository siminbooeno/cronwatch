"""Generate and dispatch periodic digest reports via configured alert channels."""

from __future__ import annotations

import datetime
from pathlib import Path
from typing import Optional

from cronwatch.alerts import dispatch_alert
from cronwatch.config import CronwatchConfig
from cronwatch.digest import DigestReport


_REPORT_TIMESTAMP_FILE = ".last_report"


def _utcnow() -> datetime.datetime:
    return datetime.datetime.now(datetime.timezone.utc)


def _read_last_report_time(state_dir: Path) -> Optional[datetime.datetime]:
    """Return the UTC datetime of the last sent report, or None."""
    ts_file = state_dir / _REPORT_TIMESTAMP_FILE
    if not ts_file.exists():
        return None
    try:
        raw = ts_file.read_text().strip()
        return datetime.datetime.fromisoformat(raw)
    except (ValueError, OSError):
        return None


def _write_last_report_time(state_dir: Path, dt: datetime.datetime) -> None:
    ts_file = state_dir / _REPORT_TIMESTAMP_FILE
    ts_file.write_text(dt.isoformat())


def is_report_due(
    state_dir: Path,
    interval_hours: int,
) -> bool:
    """Return True if enough time has elapsed since the last report."""
    last = _read_last_report_time(state_dir)
    if last is None:
        return True
    elapsed = _utcnow() - last
    return elapsed >= datetime.timedelta(hours=interval_hours)


def send_digest_report(
    cfg: CronwatchConfig,
    state_dir: Path,
    history_dir: Path,
) -> None:
    """Build a digest report and dispatch it via all configured alert channels."""
    report = DigestReport.build(cfg.jobs, state_dir, history_dir)
    subject = (
        f"[cronwatch] Digest: {report.healthy_count()} healthy, "
        f"{report.unhealthy_count()} unhealthy"
    )
    body = report.as_text()
    dispatch_alert(cfg.alert, subject=subject, body=body)
    _write_last_report_time(state_dir, _utcnow())


def maybe_send_digest(
    cfg: CronwatchConfig,
    state_dir: Path,
    history_dir: Path,
    interval_hours: int = 24,
) -> bool:
    """Send a digest report if the interval has elapsed. Returns True if sent."""
    if not is_report_due(state_dir, interval_hours):
        return False
    send_digest_report(cfg, state_dir, history_dir)
    return True
