"""CLI for inspecting job priority policies."""
from __future__ import annotations

import argparse
import sys
from typing import List

from cronwatch.config import load_config
from cronwatch.job_priority import parse_priority_policies, jobs_by_priority, PRIORITY_LEVELS


def _build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        prog="cronwatch-priority",
        description="Inspect job priority policies.",
    )
    p.add_argument("--config", required=True, help="Path to config file")
    sub = p.add_subparsers(dest="command")

    sub.add_parser("list", help="List all jobs with their priority level")

    show = sub.add_parser("show", help="Show priority policy for a specific job")
    show.add_argument("job", help="Job name")

    return p


def cmd_list(args) -> int:
    cfg = load_config(args.config)
    policies = parse_priority_policies(cfg)
    sorted_jobs = jobs_by_priority(cfg.jobs, policies)
    if not sorted_jobs:
        print("No jobs configured.")
        return 0
    print(f"{'JOB':<30} {'PRIORITY':<10} {'ALERT_MISS':<12} {'ALERT_FAIL':<12} {'MIN_FAIL'}")
    print("-" * 72)
    for job in sorted_jobs:
        pol = policies[job.name]
        print(
            f"{job.name:<30} {pol.level:<10} {str(pol.alert_on_miss):<12}"
            f" {str(pol.alert_on_failure):<12} {pol.min_failures_before_alert}"
        )
    return 0


def cmd_show(args) -> int:
    cfg = load_config(args.config)
    policies = parse_priority_policies(cfg)
    if args.job not in policies:
        print(f"Job '{args.job}' not found.", file=sys.stderr)
        return 1
    pol = policies[args.job]
    print(f"Job:                     {args.job}")
    print(f"Priority level:          {pol.level}")
    print(f"Alert on miss:           {pol.alert_on_miss}")
    print(f"Alert on failure:        {pol.alert_on_failure}")
    print(f"Min failures for alert:  {pol.min_failures_before_alert}")
    return 0


def main(argv: List[str] | None = None) -> None:
    parser = _build_parser()
    args = parser.parse_args(argv)
    if not args.command:
        parser.print_help()
        sys.exit(1)
    dispatch = {"list": cmd_list, "show": cmd_show}
    sys.exit(dispatch[args.command](args))


if __name__ == "__main__":
    main()
