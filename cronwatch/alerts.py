"""Alert dispatchers: send notifications via webhook or email."""

import json
import smtplib
import urllib.request
from email.mime.text import MIMEText
from typing import Optional

from cronwatch.config import AlertConfig


def _build_message(job_id: str, status: str, detail: str = "") -> str:
    parts = [f"[cronwatch] Job '{job_id}' — {status}"]
    if detail:
        parts.append(detail)
    return "\n".join(parts)


def send_webhook(url: str, job_id: str, status: str, detail: str = "") -> bool:
    payload = json.dumps(
        {"job_id": job_id, "status": status, "detail": detail}
    ).encode()
    req = urllib.request.Request(
        url,
        data=payload,
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=10) as resp:
            return resp.status < 400
    except Exception:
        return False


def send_email(
    smtp_host: str,
    smtp_port: int,
    sender: str,
    recipient: str,
    job_id: str,
    status: str,
    detail: str = "",
    username: Optional[str] = None,
    password: Optional[str] = None,
) -> bool:
    subject = f"[cronwatch] Job '{job_id}' {status}"
    body = _build_message(job_id, status, detail)
    msg = MIMEText(body)
    msg["Subject"] = subject
    msg["From"] = sender
    msg["To"] = recipient
    try:
        with smtplib.SMTP(smtp_host, smtp_port, timeout=10) as server:
            if username and password:
                server.starttls()
                server.login(username, password)
            server.sendmail(sender, [recipient], msg.as_string())
        return True
    except Exception:
        return False


def dispatch_alert(
    alert: AlertConfig,
    job_id: str,
    status: str,
    detail: str = "",
) -> None:
    if alert.webhook_url:
        send_webhook(alert.webhook_url, job_id, status, detail)
    if alert.email_recipient and alert.smtp_host:
        send_email(
            smtp_host=alert.smtp_host,
            smtp_port=alert.smtp_port,
            sender=alert.email_sender or "cronwatch@localhost",
            recipient=alert.email_recipient,
            job_id=job_id,
            status=status,
            detail=detail,
            username=alert.smtp_username,
            password=alert.smtp_password,
        )
