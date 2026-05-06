"""Run a cron job command and record its outcome in state and history."""

from __future__ import annotations

import subprocess
import time
from typing import Optional

from cronwatch.config import JobConfig
from cronwatch.history import append_execution
from cronwatch.state import load_store, record_failure, record_success, save_store


def run_job(
    job: JobConfig,
    state_dir: str,
    alert_config=None,
) -> bool:
    """Execute *job* and persist success/failure state.

    Returns True on success, False on failure.
    """
    store = load_store(state_dir)
    timeout: Optional[int] = job.timeout

    start = time.monotonic()
    try:
        result = subprocess.run(
            job.command,
            shell=True,
            timeout=timeout,
            capture_output=True,
            text=True,
        )
        duration = time.monotonic() - start
        success = result.returncode == 0
    except subprocess.TimeoutExpired:
        duration = time.monotonic() - start
        success = False
        result = None

    exit_code = result.returncode if result is not None else None
    note: Optional[str] = None
    if result is not None and not success and result.stderr:
        note = result.stderr.strip()[:200]
    elif result is None:
        note = f"timed out after {timeout}s"

    if success:
        record_success(store, job.name)
    else:
        record_failure(store, job.name)

    save_store(state_dir, store)

    append_execution(
        state_dir,
        job.name,
        success=success,
        exit_code=exit_code,
        duration_seconds=round(duration, 3),
        note=note,
    )

    if not success and alert_config is not None:
        from cronwatch.alerts import dispatch_alert

        dispatch_alert(
            alert_config,
            job_name=job.name,
            reason="failure",
            detail=note or f"exited with code {exit_code}",
        )

    return success
