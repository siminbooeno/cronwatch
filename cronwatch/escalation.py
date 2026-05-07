"""Escalation policy: send alerts to additional targets after N consecutive failures."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import List, Optional

from cronwatch.config import JobConfig, AlertConfig
from cronwatch.history import JobHistory
from cronwatch.alerts import dispatch_alert


@dataclass
class EscalationPolicy:
    """Defines when and how to escalate alerts for a job."""
    threshold: int  # consecutive failures before escalating
    alert: AlertConfig  # escalation-specific alert target
    reason: Optional[str] = None


def _parse_escalation(raw: dict) -> EscalationPolicy:
    """Parse a single escalation policy dict."""
    threshold = int(raw.get("threshold", 3))
    alert_raw = raw.get("alert", {})
    alert = AlertConfig(
        webhook_url=alert_raw.get("webhook_url"),
        email_to=alert_raw.get("email_to"),
        email_from=alert_raw.get("email_from"),
        smtp_host=alert_raw.get("smtp_host", "localhost"),
        smtp_port=int(alert_raw.get("smtp_port", 25)),
    )
    return EscalationPolicy(
        threshold=threshold,
        alert=alert,
        reason=raw.get("reason"),
    )


def parse_escalation_policies(job_raw: dict) -> List[EscalationPolicy]:
    """Extract escalation policies from a raw job config dict."""
    return [_parse_escalation(e) for e in job_raw.get("escalations", [])]


def check_and_escalate(
    job: JobConfig,
    policies: List[EscalationPolicy],
    history_dir: str,
) -> List[EscalationPolicy]:
    """Check consecutive failures and dispatch escalation alerts as needed.

    Returns the list of policies that were triggered.
    """
    if not policies:
        return []

    hist = JobHistory(job.name, history_dir)
    consecutive = hist.consecutive_failures()
    triggered: List[EscalationPolicy] = []

    for policy in policies:
        if consecutive >= policy.threshold:
            reason = policy.reason or f"{consecutive} consecutive failures"
            message = (
                f"[ESCALATION] Job '{job.name}' has failed {consecutive} times in a row.\n"
                f"Reason: {reason}"
            )
            dispatch_alert(policy.alert, job.name, message)
            triggered.append(policy)

    return triggered
