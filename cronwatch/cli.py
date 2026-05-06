"""CLI entry-point for cronwatch."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from cronwatch.config import load_config
from cronwatch.runner import run_job
from cronwatch.checker import check_jobs
from cronwatch.alerts import dispatch_alert
from cronwatch.retention import prune_all_history, prune_state


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="cronwatch",
        description="Lightweight cron job monitor",
    )
    parser.add_argument("--config", default="cronwatch.json", help="Config file path")
    parser.add_argument("--state-dir", default=".cronwatch/state", help="State directory")
    parser.add_argument("--history-dir", default=".cronwatch/history", help="History directory")

    sub = parser.add_subparsers(dest="command")

    run_p = sub.add_parser("run", help="Run a named job and record outcome")
    run_p.add_argument("job", help="Job name")

    sub.add_parser("check", help="Check for overdue jobs and dispatch alerts")

    prune_p = sub.add_parser("prune", help="Prune old history and stale state")
    prune_p.add_argument(
        "--max-age-days", type=int, default=30, help="Retention window in days"
    )

    return parser


def cmd_run(args: argparse.Namespace) -> int:
    cfg = load_config(args.config)
    job_cfg = next((j for j in cfg.jobs if j.name == args.job), None)
    if job_cfg is None:
        print(f"cronwatch: unknown job '{args.job}'", file=sys.stderr)
        return 2

    Path(args.state_dir).mkdir(parents=True, exist_ok=True)
    Path(args.history_dir).mkdir(parents=True, exist_ok=True)

    ok = run_job(job_cfg, state_dir=args.state_dir, history_dir=args.history_dir)
    return 0 if ok else 1


def cmd_check(args: argparse.Namespace) -> int:
    cfg = load_config(args.config)
    overdue = check_jobs(cfg.jobs, state_dir=args.state_dir)
    for job_name in overdue:
        dispatch_alert(cfg.alert, job_name=job_name, reason="overdue")
    return 0


def cmd_prune(args: argparse.Namespace) -> int:
    cfg = load_config(args.config)
    job_names = [j.name for j in cfg.jobs]

    history_results = prune_all_history(
        history_dir=args.history_dir,
        max_age_days=args.max_age_days,
        job_names=job_names,
    )
    for name, count in history_results.items():
        if count:
            print(f"pruned {count} history record(s) for '{name}'")

    removed_states = 0
    for name in job_names:
        if prune_state(args.state_dir, args.max_age_days, name):
            print(f"removed stale state for '{name}'")
            removed_states += 1

    if not any(history_results.values()) and removed_states == 0:
        print("nothing to prune")

    return 0


def main(argv: list[str] | None = None) -> int:
    parser = _build_parser()
    args = parser.parse_args(argv)

    if args.command == "run":
        return cmd_run(args)
    if args.command == "check":
        return cmd_check(args)
    if args.command == "prune":
        return cmd_prune(args)

    parser.print_help()
    return 0


if __name__ == "__main__":
    sys.exit(main())
