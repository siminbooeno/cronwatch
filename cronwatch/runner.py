"""Runner module: executes a shell command and records success/failure in state."""

import subprocess
import time
import logging
from typing import Optional

from cronwatch.config import JobConfig
from cronwatch.state import record_success, record_failure

logger = logging.getLogger(__name__)


def run_job(job: JobConfig, state_dir: str = ".cronwatch") -> bool:
    """
    Execute the command associated with *job*.

    Returns True on success (exit code 0), False otherwise.
    Respects job.timeout_seconds when set.
    Records the outcome in the persistent state store.
    """
    if not job.command:
        logger.warning("Job '%s' has no command configured – skipping.", job.name)
        return False

    timeout: Optional[float] = (
        float(job.timeout_seconds) if job.timeout_seconds is not None else None
    )

    logger.info("Running job '%s': %s", job.name, job.command)
    start = time.monotonic()

    try:
        result = subprocess.run(
            job.command,
            shell=True,
            capture_output=True,
            text=True,
            timeout=timeout,
        )
        elapsed = time.monotonic() - start

        if result.returncode == 0:
            logger.info(
                "Job '%s' succeeded in %.2fs.", job.name, elapsed
            )
            record_success(job.name, state_dir=state_dir)
            return True
        else:
            logger.error(
                "Job '%s' failed (exit %d) after %.2fs.\nstdout: %s\nstderr: %s",
                job.name,
                result.returncode,
                elapsed,
                result.stdout.strip(),
                result.stderr.strip(),
            )
            record_failure(job.name, state_dir=state_dir)
            return False

    except subprocess.TimeoutExpired:
        elapsed = time.monotonic() - start
        logger.error(
            "Job '%s' timed out after %.2fs (limit: %ss).",
            job.name,
            elapsed,
            job.timeout_seconds,
        )
        record_failure(job.name, state_dir=state_dir)
        return False

    except Exception as exc:  # pragma: no cover
        logger.exception("Unexpected error running job '%s': %s", job.name, exc)
        record_failure(job.name, state_dir=state_dir)
        return False
