"""Command-line interface for cronwatch."""

from __future__ import annotations

import argparse
import logging
import sys
from pathlib import Path

from cronwatch.alerts import dispatch_alert
from cronwatch.checker import check_jobs, record_heartbeat
from cronwatch.config import load_config
from cronwatch.retention import prune_all_history, prune_state
from cronwatch.runner import run_job
from cronwatch.scheduler import run_scheduler

logger = logging.getLogger(__name__)


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="cronwatch", description="Cron job monitor")
    parser.add_argument("--config", default="cronwatch.json", help="Config file path")
    parser.add_argument("--state-dir", default=".cronwatch/state", help="State directory")
    parser.add_argument("-v", "--verbose", action="store_true")

    sub = parser.add_subparsers(dest="command", required=True)

    run_p = sub.add_parser("run", help="Run a job and record its outcome")
    run_p.add_argument("job", help="Job name defined in config")

    check_p = sub.add_parser("check", help="Check all jobs for missed executions")
    check_p.add_argument("--alert", action="store_true", help="Dispatch alerts for overdue jobs")

    sub.add_parser("prune", help="Prune old history and state entries")

    watch_p = sub.add_parser("watch", help="Run the periodic scheduler daemon")
    watch_p.add_argument(
        "--interval",
        type=int,
        default=60,
        help="Seconds between checks (default: 60)",
    )

    return parser


def cmd_run(args: argparse.Namespace) -> int:
    config = load_config(args.config)
    state_dir = Path(args.state_dir)
    job_cfg = next((j for j in config.jobs if j.name == args.job), None)
    if job_cfg is None:
        print(f"Unknown job: {args.job}", file=sys.stderr)
        return 2
    success = run_job(job_cfg, state_dir)
    return 0 if success else 1


def cmd_check(args: argparse.Namespace) -> int:
    config = load_config(args.config)
    state_dir = Path(args.state_dir)
    overdue = check_jobs(config.jobs, state_dir)
    if not overdue:
        print("All jobs OK")
        return 0
    for job_name, reason in overdue:
        print(f"OVERDUE  {job_name}: {reason}")
        if args.alert:
            dispatch_alert(config.alert, job_name=job_name, event="miss", detail=reason)
    return 1


def cmd_prune(args: argparse.Namespace) -> int:
    config = load_config(args.config)
    state_dir = Path(args.state_dir)
    history_dir = state_dir.parent / "history"
    prune_all_history(config.jobs, history_dir)
    prune_state(config.jobs, state_dir)
    print("Prune complete")
    return 0


def cmd_watch(args: argparse.Namespace) -> int:
    config = load_config(args.config)
    state_dir = Path(args.state_dir)
    run_scheduler(config, state_dir, poll_interval=args.interval)
    return 0


def main(argv: list[str] | None = None) -> None:
    parser = _build_parser()
    args = parser.parse_args(argv)

    logging.basicConfig(
        level=logging.DEBUG if args.verbose else logging.INFO,
        format="%(asctime)s %(levelname)s %(name)s: %(message)s",
    )

    dispatch = {
        "run": cmd_run,
        "check": cmd_check,
        "prune": cmd_prune,
        "watch": cmd_watch,
    }
    sys.exit(dispatch[args.command](args))


if __name__ == "__main__":  # pragma: no cover
    main()
