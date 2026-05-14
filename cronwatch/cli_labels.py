"""CLI tool for querying jobs by labels."""
from __future__ import annotations

import argparse
import sys

from cronwatch.config import load_config
from cronwatch.labels import (
    all_label_keys,
    all_label_values,
    jobs_matching_selector,
    parse_selector,
)


def _build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        prog="cronwatch-labels",
        description="Query cron jobs by key-value labels.",
    )
    p.add_argument("--config", required=True, help="Path to cronwatch config file")
    sub = p.add_subparsers(dest="command", required=True)

    sel = sub.add_parser("select", help="List jobs matching a label selector")
    sel.add_argument(
        "selector",
        help="Comma-separated key=value pairs, e.g. env=prod,team=infra",
    )

    sub.add_parser("keys", help="List all label keys used across jobs")

    vals = sub.add_parser("values", help="List all values for a given label key")
    vals.add_argument("key", help="Label key to inspect")

    return p


def cmd_select(args: argparse.Namespace) -> int:
    cfg = load_config(args.config)
    try:
        selector = parse_selector(args.selector)
    except ValueError as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 1
    matches = jobs_matching_selector(cfg, selector)
    if not matches:
        print("No jobs match the given selector.")
        return 0
    for job in matches:
        label_str = ", ".join(f"{k}={v}" for k, v in sorted(job.labels.items()))
        print(f"  {job.name}  [{label_str}]")
    return 0


def cmd_keys(args: argparse.Namespace) -> int:
    cfg = load_config(args.config)
    keys = all_label_keys(cfg)
    if not keys:
        print("No labels defined.")
        return 0
    for k in keys:
        print(f"  {k}")
    return 0


def cmd_values(args: argparse.Namespace) -> int:
    cfg = load_config(args.config)
    values = all_label_values(cfg, args.key)
    if not values:
        print(f"No values found for label key {args.key!r}.")
        return 0
    for v in values:
        print(f"  {v}")
    return 0


def main() -> None:
    parser = _build_parser()
    args = parser.parse_args()
    dispatch = {"select": cmd_select, "keys": cmd_keys, "values": cmd_values}
    sys.exit(dispatch[args.command](args))


if __name__ == "__main__":
    main()
