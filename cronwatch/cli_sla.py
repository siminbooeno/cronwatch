"""CLI commands for inspecting SLA status."""
from __future__ import annotations

import argparse
import json
import sys

from cronwatch.config import load_config
from cronwatch.sla import check_all_slas, check_sla


def _build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        prog="cronwatch-sla",
        description="Inspect SLA compliance for cron jobs.",
    )
    p.add_argument("--config", required=True, help="Path to config file")
    p.add_argument("--history-dir", required=True, help="Path to history directory")

    sub = p.add_subparsers(dest="command")

    chk = sub.add_parser("check", help="Print SLA violations (exits 1 if any)")
    chk.add_argument("--job", default=None, help="Check a single job by name")
    chk.add_argument("--json", dest="as_json", action="store_true")

    return p


def cmd_check(args) -> int:
    cfg = load_config(args.config)

    if args.job:
        jobs = [j for j in cfg.jobs if j.name == args.job]
        if not jobs:
            print(f"Job '{args.job}' not found in config.", file=sys.stderr)
            return 2
    else:
        jobs = cfg.jobs

    violations = check_all_slas(jobs, args.history_dir)

    if args.as_json:
        data = [
            {
                "job": v.job_name,
                "reason": v.reason,
                "current": round(v.current_value, 4),
                "threshold": round(v.threshold, 4),
            }
            for v in violations
        ]
        print(json.dumps(data, indent=2))
    else:
        if not violations:
            print("All SLAs satisfied.")
        else:
            for v in violations:
                print(
                    f"[VIOLATION] {v.job_name}: {v.reason} "
                    f"(current={v.current_value:.3f}, threshold={v.threshold:.3f})"
                )

    return 1 if violations else 0


def main(argv=None) -> None:
    parser = _build_parser()
    args = parser.parse_args(argv)
    if args.command == "check":
        sys.exit(cmd_check(args))
    else:
        parser.print_help()
        sys.exit(0)


if __name__ == "__main__":
    main()
