"""CLI entry-point for inspecting cronwatch runtime metrics."""
from __future__ import annotations

import argparse
import json
import sys
from typing import List, Optional

from cronwatch.metrics import all_counters, reset_counter


def _build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        prog="cronwatch-metrics",
        description="Inspect or reset cronwatch runtime metrics.",
    )
    p.add_argument("--state-dir", default=".cronwatch", help="State directory")
    sub = p.add_subparsers(dest="command")

    sub.add_parser("show", help="Print all counters")

    show_json = sub.add_parser("json", help="Print counters as JSON")
    show_json  # noqa: B018

    reset = sub.add_parser("reset", help="Reset a specific counter")
    reset.add_argument("key", help="Counter key to reset")

    sub.add_parser("reset-all", help="Reset every counter")
    return p


def cmd_show(state_dir: str) -> int:
    counters = all_counters(state_dir)
    if not counters:
        print("No metrics recorded yet.")
        return 0
    width = max(len(k) for k in counters)
    for key in sorted(counters):
        print(f"{key:<{width}}  {counters[key]}")
    return 0


def cmd_json(state_dir: str) -> int:
    print(json.dumps(all_counters(state_dir), indent=2))
    return 0


def cmd_reset(state_dir: str, key: str) -> int:
    reset_counter(state_dir, key)
    print(f"Counter '{key}' reset to 0.")
    return 0


def cmd_reset_all(state_dir: str) -> int:
    counters = all_counters(state_dir)
    for key in counters:
        reset_counter(state_dir, key)
    print(f"Reset {len(counters)} counter(s).")
    return 0


def main(argv: Optional[List[str]] = None) -> int:
    parser = _build_parser()
    args = parser.parse_args(argv)
    if args.command == "show":
        return cmd_show(args.state_dir)
    if args.command == "json":
        return cmd_json(args.state_dir)
    if args.command == "reset":
        return cmd_reset(args.state_dir, args.key)
    if args.command == "reset-all":
        return cmd_reset_all(args.state_dir)
    parser.print_help()
    return 1


if __name__ == "__main__":
    sys.exit(main())
