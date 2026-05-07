"""Webhook delivery with retry logic and exponential backoff.

Provides a resilient webhook sender that retries on transient failures,
respecting configurable attempt limits and backoff parameters.
"""

from __future__ import annotations

import logging
import time
from dataclasses import dataclass, field
from typing import Optional

import requests

logger = logging.getLogger(__name__)

# Default retry settings
DEFAULT_MAX_ATTEMPTS = 3
DEFAULT_BACKOFF_BASE = 2.0   # seconds
DEFAULT_BACKOFF_MAX = 60.0   # seconds
DEFAULT_TIMEOUT = 10         # seconds per request

# HTTP status codes considered transient (worth retrying)
_RETRYABLE_STATUSES = {429, 500, 502, 503, 504}


@dataclass
class RetryPolicy:
    """Configuration for webhook retry behaviour."""

    max_attempts: int = DEFAULT_MAX_ATTEMPTS
    backoff_base: float = DEFAULT_BACKOFF_BASE
    backoff_max: float = DEFAULT_BACKOFF_MAX
    timeout: int = DEFAULT_TIMEOUT
    # Optional list of additional HTTP status codes to retry on
    extra_retryable_statuses: list[int] = field(default_factory=list)

    @property
    def retryable_statuses(self) -> frozenset[int]:
        return _RETRYABLE_STATUSES | frozenset(self.extra_retryable_statuses)


@dataclass
class DeliveryResult:
    """Outcome of a webhook delivery attempt sequence."""

    success: bool
    attempts: int
    last_status_code: Optional[int] = None
    last_error: Optional[str] = None


def _backoff_delay(attempt: int, base: float, maximum: float) -> float:
    """Return exponential backoff delay (seconds) for the given attempt index (0-based)."""
    delay = base ** attempt
    return min(delay, maximum)


def send_webhook_with_retry(
    url: str,
    payload: dict,
    policy: Optional[RetryPolicy] = None,
    *,
    _sleep: callable = time.sleep,  # injectable for testing
) -> DeliveryResult:
    """POST *payload* as JSON to *url*, retrying on transient failures.

    Args:
        url:     Destination webhook URL.
        payload: JSON-serialisable dict to send as the request body.
        policy:  :class:`RetryPolicy` controlling retry behaviour.  Uses
                 module defaults when *None*.
        _sleep:  Callable used for sleeping between retries; injectable so
                 tests can avoid real delays.

    Returns:
        A :class:`DeliveryResult` describing the final outcome.
    """
    if policy is None:
        policy = RetryPolicy()

    last_status: Optional[int] = None
    last_error: Optional[str] = None

    for attempt in range(policy.max_attempts):
        try:
            response = requests.post(
                url,
                json=payload,
                timeout=policy.timeout,
            )
            last_status = response.status_code

            if response.ok:
                logger.debug(
                    "Webhook delivered on attempt %d/%d (status %d)",
                    attempt + 1,
                    policy.max_attempts,
                    last_status,
                )
                return DeliveryResult(
                    success=True,
                    attempts=attempt + 1,
                    last_status_code=last_status,
                )

            if last_status not in policy.retryable_statuses:
                # Non-retryable HTTP error — fail immediately
                last_error = f"HTTP {last_status}"
                logger.warning(
                    "Webhook returned non-retryable status %d; giving up.",
                    last_status,
                )
                break

            last_error = f"HTTP {last_status}"
            logger.warning(
                "Webhook attempt %d/%d failed with status %d.",
                attempt + 1,
                policy.max_attempts,
                last_status,
            )

        except requests.RequestException as exc:
            last_error = str(exc)
            logger.warning(
                "Webhook attempt %d/%d raised exception: %s",
                attempt + 1,
                policy.max_attempts,
                exc,
            )

        # Sleep before the next attempt (skip after the last one)
        if attempt + 1 < policy.max_attempts:
            delay = _backoff_delay(attempt, policy.backoff_base, policy.backoff_max)
            logger.debug("Retrying webhook in %.1f seconds…", delay)
            _sleep(delay)

    logger.error(
        "Webhook delivery failed after %d attempt(s): %s",
        policy.max_attempts,
        last_error,
    )
    return DeliveryResult(
        success=False,
        attempts=policy.max_attempts,
        last_status_code=last_status,
        last_error=last_error,
    )
