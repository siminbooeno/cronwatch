"""CLI commands to inspect per-job retention policies."""
from __future__ import annotations

import argparse
import json
import sys
from typing import List

from cronwatch.config import load_config
from cronwatch.retention_policy import parse_retention_policies, effective_policy


def _build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        prog="cronwatch-retention-policy",
        description="Inspect per-job retention policies.",
    )
    p.add_argument("--config", required=True, help="Path to cronwatch config file")
    sub = p.add_subparsers(dest="command")

    show = sub.add_parser("show", help="Show retention policy for one or all jobs")
    show.add_argument("job", nargs="?", default=None, help="Job name (omit for all)")
    show.add_argument("--json", dest="as_json", action="store_true")

    return p


def cmd_show(args: argparse.Namespace) -> int:
    cfg = load_config(args.config)
    policies = parse_retention_policies(cfg)

    if args.job:
        job_names = [args.job]
    else:
        job_names = [j.name for j in cfg.jobs]

    rows = []
    for name in job_names:
        pol = effective_policy(name, policies)
        rows.append({
            "job": name,
            "history_days": pol.history_days,
            "max_records": pol.max_records,
            "state_days": pol.state_days,
        })

    if getattr(args, "as_json", False):
        print(json.dumps(rows, indent=2))
    else:
        header = f"{'JOB':<30} {'HISTORY_DAYS':>12} {'MAX_RECORDS':>12} {'STATE_DAYS':>10}"
        print(header)
        print("-" * len(header))
        for r in rows:
            mr = str(r["max_records"]) if r["max_records"] is not None else "unlimited"
            print(f"{r['job']:<30} {r['history_days']:>12} {mr:>12} {r['state_days']:>10}")
    return 0


def main(argv: List[str] | None = None) -> None:
    parser = _build_parser()
    args = parser.parse_args(argv)
    if args.command == "show":
        sys.exit(cmd_show(args))
    else:
        parser.print_help()
        sys.exit(1)


if __name__ == "__main__":
    main()
