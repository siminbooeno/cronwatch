"""CLI entry-point for cronwatch.

Usage:
    cronwatch run  --config <path> [--state-dir <dir>]
    cronwatch check --config <path> [--state-dir <dir>]
"""

import argparse
import logging
import sys

from cronwatch.config import load_config
from cronwatch.runner import run_job
from cronwatch.checker import check_jobs
from cronwatch.alerts import dispatch_alert

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(name)s – %(message)s",
)
logger = logging.getLogger(__name__)


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="cronwatch",
        description="Lightweight cron job monitor.",
    )
    parser.add_argument("-c", "--config", required=True, help="Path to config JSON file.")
    parser.add_argument(
        "--state-dir", default=".cronwatch", help="Directory for state files (default: .cronwatch)."
    )

    sub = parser.add_subparsers(dest="command", required=True)

    sub.add_parser("run", help="Execute all configured jobs and record outcomes.")
    sub.add_parser("check", help="Check for missed/overdue jobs and dispatch alerts.")

    return parser


def cmd_run(config_path: str, state_dir: str) -> int:
    cfg = load_config(config_path)
    exit_code = 0
    for job in cfg.jobs:
        ok = run_job(job, state_dir=state_dir)
        if not ok:
            exit_code = 1
            if cfg.alert:
                dispatch_alert(
                    cfg.alert,
                    subject=f"[cronwatch] Job '{job.name}' FAILED",
                    body=f"Job '{job.name}' exited with a non-zero status or timed out.",
                )
    return exit_code


def cmd_check(config_path: str, state_dir: str) -> int:
    cfg = load_config(config_path)
    overdue = check_jobs(cfg.jobs, state_dir=state_dir)
    if overdue and cfg.alert:
        for job_name in overdue:
            dispatch_alert(
                cfg.alert,
                subject=f"[cronwatch] Job '{job_name}' is OVERDUE",
                body=f"Job '{job_name}' has not been seen within its expected schedule.",
            )
    return 1 if overdue else 0


def main(argv=None) -> None:
    parser = _build_parser()
    args = parser.parse_args(argv)

    if args.command == "run":
        sys.exit(cmd_run(args.config, args.state_dir))
    elif args.command == "check":
        sys.exit(cmd_check(args.config, args.state_dir))
