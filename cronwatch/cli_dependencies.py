"""CLI: inspect job dependency status."""

from __future__ import annotations

import argparse
import sys

from cronwatch.config import load_config
from cronwatch.dependencies import check_dependencies, filter_ready_jobs


def _build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        prog="cronwatch-deps",
        description="Inspect job dependency satisfaction.",
    )
    p.add_argument("--config", required=True, help="Path to cronwatch config JSON")
    p.add_argument("--state-dir", required=True, help="State/history directory")
    sub = p.add_subparsers(dest="command")

    check = sub.add_parser("check", help="Check dependencies for a specific job")
    check.add_argument("job", help="Job name")

    sub.add_parser("ready", help="List jobs whose dependencies are satisfied")
    return p


def cmd_check(args: argparse.Namespace) -> int:
    cfg = load_config(args.config)
    job_map = {j.name: j for j in cfg.jobs}
    if args.job not in job_map:
        print(f"Unknown job: {args.job}", file=sys.stderr)
        return 2
    result = check_dependencies(job_map[args.job], cfg, args.state_dir)
    if result.satisfied:
        print(f"{args.job}: OK (all dependencies satisfied)")
        return 0
    print(f"{args.job}: BLOCKED — {result.reason}")
    return 1


def cmd_ready(args: argparse.Namespace) -> int:
    cfg = load_config(args.config)
    ready = filter_ready_jobs(cfg.jobs, cfg, args.state_dir)
    if not ready:
        print("No jobs are ready.")
        return 0
    for j in ready:
        print(j.name)
    return 0


def main(argv=None) -> None:
    parser = _build_parser()
    args = parser.parse_args(argv)
    if args.command == "check":
        sys.exit(cmd_check(args))
    elif args.command == "ready":
        sys.exit(cmd_ready(args))
    else:
        parser.print_help()
        sys.exit(1)


if __name__ == "__main__":
    main()
