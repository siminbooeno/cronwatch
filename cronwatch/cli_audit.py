"""CLI sub-commands for inspecting the cronwatch audit log."""

from __future__ import annotations

import argparse
import sys
from typing import List, Optional

from cronwatch.audit_log import append_event, read_events, prune_audit_log


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="cronwatch-audit",
        description="Inspect and manage the cronwatch audit log.",
    )
    parser.add_argument(
        "--state-dir",
        default="/var/lib/cronwatch",
        help="Directory where state and audit log are stored.",
    )
    sub = parser.add_subparsers(dest="command", required=True)

    # list sub-command
    ls_p = sub.add_parser("list", help="List audit log entries.")
    ls_p.add_argument("--event", default=None, help="Filter by event type.")
    ls_p.add_argument("--job", default=None, help="Filter by job name.")
    ls_p.add_argument(
        "--limit", type=int, default=50, help="Maximum number of entries to show."
    )

    # prune sub-command
    prune_p = sub.add_parser("prune", help="Remove old audit log entries.")
    prune_p.add_argument(
        "--keep-days",
        type=int,
        default=30,
        help="Retain entries newer than this many days.",
    )

    return parser


def cmd_list(args: argparse.Namespace) -> int:
    events = read_events(
        args.state_dir,
        event_type=args.event,
        job_name=args.job,
        limit=args.limit,
    )
    if not events:
        print("No audit log entries found.")
        return 0

    for record in events:
        job_part = f"  job={record['job']}" if "job" in record else ""
        details_part = ""
        if "details" in record:
            kv = ", ".join(f"{k}={v}" for k, v in record["details"].items())
            details_part = f"  [{kv}]"
        print(f"{record['ts']}  {record['event']}{job_part}{details_part}")
    return 0


def cmd_prune(args: argparse.Namespace) -> int:
    removed = prune_audit_log(args.state_dir, keep_days=args.keep_days)
    print(f"Pruned {removed} audit log entries older than {args.keep_days} days.")
    return 0


def main(argv: Optional[List[str]] = None) -> None:
    parser = _build_parser()
    args = parser.parse_args(argv)

    dispatch = {
        "list": cmd_list,
        "prune": cmd_prune,
    }
    handler = dispatch.get(args.command)
    if handler is None:
        parser.print_help()
        sys.exit(1)

    sys.exit(handler(args))


if __name__ == "__main__":  # pragma: no cover
    main()
