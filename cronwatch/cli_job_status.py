"""CLI entry-point: ``cronwatch-status`` — show per-job status."""
from __future__ import annotations

import argparse
import json
import sys

from cronwatch.config import load_config
from cronwatch.job_status import get_all_statuses, format_status_table


def _build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        prog="cronwatch-status",
        description="Show current status for all monitored cron jobs.",
    )
    p.add_argument("--config", required=True, help="Path to cronwatch config JSON.")
    p.add_argument("--history-dir", required=True, help="Directory containing job history.")
    sub = p.add_subparsers(dest="cmd")

    show = sub.add_parser("show", help="Print a status table (default).")
    show.add_argument("--job", default=None, help="Filter to a single job name.")

    jcmd = sub.add_parser("json", help="Emit status as JSON.")
    jcmd.add_argument("--job", default=None, help="Filter to a single job name.")
    return p


def cmd_show(args: argparse.Namespace) -> int:
    cfg = load_config(args.config)
    statuses = get_all_statuses(cfg, args.history_dir)
    if getattr(args, "job", None):
        statuses = [s for s in statuses if s.job_name == args.job]
        if not statuses:
            print(f"Job '{args.job}' not found.", file=sys.stderr)
            return 1
    print(format_status_table(statuses))
    return 0


def cmd_json(args: argparse.Namespace) -> int:
    cfg = load_config(args.config)
    statuses = get_all_statuses(cfg, args.history_dir)
    if getattr(args, "job", None):
        statuses = [s for s in statuses if s.job_name == args.job]
    payload = [
        {
            "job": s.job_name,
            "status": s.status,
            "total_runs": s.total_runs,
            "success_rate": round(s.success_rate, 4),
            "consecutive_failures": s.consecutive_failures,
            "last_success": s.last_success,
            "last_failure": s.last_failure,
        }
        for s in statuses
    ]
    print(json.dumps(payload, indent=2))
    return 0


def main(argv: list[str] | None = None) -> None:
    parser = _build_parser()
    args = parser.parse_args(argv)
    if args.cmd == "json":
        sys.exit(cmd_json(args))
    else:
        sys.exit(cmd_show(args))


if __name__ == "__main__":
    main()
