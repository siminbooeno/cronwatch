"""CLI commands for inspecting job weight policies."""

from __future__ import annotations

import argparse
import sys

from cronwatch.job_weights import DEFAULT_WEIGHT, get_weight, load_weight_policies, rank_jobs
from cronwatch.config import load_config


def _build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        prog="cronwatch-weights",
        description="Inspect job weight / importance policies.",
    )
    p.add_argument("--config", required=True, help="Path to cronwatch config JSON")
    p.add_argument("--weights", required=True, help="Path to weights JSON file")
    sub = p.add_subparsers(dest="cmd")

    sub.add_parser("list", help="List all jobs with their weights, ranked")

    sh = sub.add_parser("show", help="Show weight for a specific job")
    sh.add_argument("job", help="Job name")

    return p


def cmd_list(args: argparse.Namespace) -> int:
    cfg = load_config(args.config)
    policies = load_weight_policies(args.weights)
    job_names = [j.name for j in cfg.jobs]
    ranked = rank_jobs(job_names, policies)
    print(f"{'JOB':<35} {'WEIGHT':>8}  REASON")
    print("-" * 60)
    for name in ranked:
        w = get_weight(name, policies)
        reason = next((p.reason or "" for p in policies if p.job_name == name), "")
        print(f"{name:<35} {w:>8.2f}  {reason}")
    return 0


def cmd_show(args: argparse.Namespace) -> int:
    policies = load_weight_policies(args.weights)
    w = get_weight(args.job, policies)
    reason = next((p.reason or "(none)" for p in policies if p.job_name == args.job), "(default)")
    print(f"job:    {args.job}")
    print(f"weight: {w:.2f}")
    print(f"reason: {reason}")
    return 0


def main(argv: list[str] | None = None) -> None:
    parser = _build_parser()
    args = parser.parse_args(argv)
    if args.cmd == "list":
        sys.exit(cmd_list(args))
    elif args.cmd == "show":
        sys.exit(cmd_show(args))
    else:
        parser.print_help()
        sys.exit(1)


if __name__ == "__main__":
    main()
