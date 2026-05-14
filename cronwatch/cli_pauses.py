"""CLI sub-commands for pausing and resuming cron jobs."""

from __future__ import annotations

import argparse
import sys
from datetime import datetime, timezone, timedelta
from typing import Optional

from cronwatch.pauses import pause_job, resume_job, is_paused, list_paused_jobs


def _build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(prog="cronwatch-pause", description="Pause / resume jobs")
    p.add_argument("--state-dir", default=".cronwatch", help="State directory")
    sub = p.add_subparsers(dest="command", required=True)

    # pause
    pp = sub.add_parser("pause", help="Pause a job")
    pp.add_argument("job", help="Job name")
    pp.add_argument("--reason", default="", help="Human-readable reason")
    pp.add_argument("--minutes", type=int, default=None, help="Pause for N minutes")
    pp.add_argument("--hours", type=int, default=None, help="Pause for N hours")

    # resume
    rp = sub.add_parser("resume", help="Resume a paused job")
    rp.add_argument("job", help="Job name")

    # status
    sp = sub.add_parser("status", help="Check whether a job is paused")
    sp.add_argument("job", help="Job name")

    # list
    sub.add_parser("list", help="List all paused jobs")

    return p


def cmd_pause(args: argparse.Namespace) -> int:
    until: Optional[datetime] = None
    minutes = getattr(args, "minutes", None)
    hours = getattr(args, "hours", None)
    if minutes:
        until = datetime.now(timezone.utc) + timedelta(minutes=minutes)
    elif hours:
        until = datetime.now(timezone.utc) + timedelta(hours=hours)

    record = pause_job(args.state_dir, args.job, reason=args.reason, until=until)
    expiry = f" until {record['until']}" if record["until"] else " indefinitely"
    print(f"Paused '{args.job}'{expiry}.")
    return 0


def cmd_resume(args: argparse.Namespace) -> int:
    removed = resume_job(args.state_dir, args.job)
    if removed:
        print(f"Resumed '{args.job}'.")
        return 0
    print(f"'{args.job}' was not paused.")
    return 1


def cmd_status(args: argparse.Namespace) -> int:
    if is_paused(args.state_dir, args.job):
        print(f"'{args.job}' is PAUSED.")
        return 0
    print(f"'{args.job}' is active (not paused).")
    return 0


def cmd_list(args: argparse.Namespace) -> int:
    records = list_paused_jobs(args.state_dir)
    if not records:
        print("No jobs are currently paused.")
        return 0
    for r in records:
        expiry = r["until"] or "indefinitely"
        reason = f" — {r['reason']}" if r["reason"] else ""
        print(f"{r['job']:30s}  until={expiry}{reason}")
    return 0


def main(argv: list[str] | None = None) -> None:
    parser = _build_parser()
    args = parser.parse_args(argv)
    dispatch = {"pause": cmd_pause, "resume": cmd_resume, "status": cmd_status, "list": cmd_list}
    sys.exit(dispatch[args.command](args))


if __name__ == "__main__":
    main()
