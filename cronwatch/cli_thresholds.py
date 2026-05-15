"""CLI: inspect threshold violations across all monitored jobs."""
from __future__ import annotations

import argparse
import sys

from cronwatch.config import load_config
from cronwatch.thresholds import check_all_thresholds, ThresholdViolation


def _build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        prog="cronwatch-thresholds",
        description="Check per-job alert thresholds and report violations.",
    )
    p.add_argument("--config", required=True, help="Path to cronwatch config file")
    p.add_argument("--history-dir", required=True, help="Path to history directory")
    p.add_argument(
        "--window",
        type=int,
        default=20,
        help="Number of recent executions to consider (default: 20)",
    )
    p.add_argument(
        "--level",
        choices=["warn", "crit"],
        default=None,
        help="Filter output to a specific severity level",
    )
    p.add_argument(
        "--exit-code",
        action="store_true",
        help="Exit with code 1 if any violations are found",
    )
    return p


def cmd_check(args: argparse.Namespace) -> int:
    cfg = load_config(args.config)
    violations = check_all_thresholds(cfg, args.history_dir, window=args.window)

    if args.level:
        violations = [v for v in violations if v.level == args.level]

    if not violations:
        print("No threshold violations found.")
        return 0

    for v in violations:
        label = "[WARN]" if v.level == "warn" else "[CRIT]"
        print(f"{label} {v.job_name}: {v.reason}")

    if args.exit_code:
        return 1
    return 0


def main() -> None:  # pragma: no cover
    parser = _build_parser()
    args = parser.parse_args()
    sys.exit(cmd_check(args))


if __name__ == "__main__":  # pragma: no cover
    main()
