"""Periodic scheduler that runs check_jobs on a configurable interval."""

from __future__ import annotations

import logging
import signal
import time
from pathlib import Path
from typing import Optional

from cronwatch.alerts import dispatch_alert
from cronwatch.checker import check_jobs
from cronwatch.config import CronwatchConfig

logger = logging.getLogger(__name__)

_STOP = False


def _handle_sigterm(signum, frame) -> None:  # noqa: ANN001
    global _STOP
    logger.info("Received signal %s, stopping scheduler.", signum)
    _STOP = True


def run_scheduler(
    config: CronwatchConfig,
    state_dir: Path,
    poll_interval: int = 60,
    once: bool = False,
) -> None:
    """Loop forever (or once), calling check_jobs and dispatching alerts.

    Args:
        config: Loaded CronwatchConfig.
        state_dir: Directory used by the state store.
        poll_interval: Seconds between successive checks.
        once: If True, run a single check and return (useful for testing).
    """
    global _STOP
    _STOP = False

    signal.signal(signal.SIGTERM, _handle_sigterm)
    signal.signal(signal.SIGINT, _handle_sigterm)

    logger.info(
        "Scheduler started. poll_interval=%ds, jobs=%d",
        poll_interval,
        len(config.jobs),
    )

    while not _STOP:
        overdue = check_jobs(config.jobs, state_dir)
        for job_name, reason in overdue:
            logger.warning("Job overdue: %s \u2014 %s", job_name, reason)
            try:
                dispatch_alert(
                    config.alert,
                    job_name=job_name,
                    event="miss",
                    detail=reason,
                )
            except Exception:  # noqa: BLE001
                logger.exception(
                    "Failed to dispatch alert for job %s; continuing.", job_name
                )

        if once:
            break

        _sleep_interruptible(poll_interval)

    logger.info("Scheduler stopped.")


def _sleep_interruptible(seconds: int) -> None:
    """Sleep in small increments so SIGTERM is handled promptly."""
    deadline = time.monotonic() + seconds
    while not _STOP and time.monotonic() < deadline:
        time.sleep(min(1.0, deadline - time.monotonic()))
