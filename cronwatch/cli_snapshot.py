"""CLI sub-commands for managing and viewing cronwatch snapshots."""

from __future__ import annotations

import argparse
import json
import os
import sys

from cronwatch.config import load_config
from cronwatch.snapshot import (
    capture_snapshot,
    diff_snapshots,
    load_snapshot,
    save_snapshot,
)


def _build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        prog="cronwatch-snapshot",
        description="Capture and compare cronwatch job snapshots.",
    )
    p.add_argument("--config", required=True, help="Path to cronwatch config JSON")
    sub = p.add_subparsers(dest="command", required=True)

    cap = sub.add_parser("capture", help="Capture a new snapshot")
    cap.add_argument("--output", required=True, help="Path to write snapshot JSON")

    diff = sub.add_parser("diff", help="Diff two snapshots")
    diff.add_argument("previous", help="Path to previous snapshot JSON")
    diff.add_argument("current", help="Path to current snapshot JSON")

    show = sub.add_parser("show", help="Pretty-print a snapshot")
    show.add_argument("snapshot", help="Path to snapshot JSON")

    return p


def cmd_capture(args: argparse.Namespace) -> int:
    cfg = load_config(args.config)
    snap = capture_snapshot(cfg, cfg.state_dir, cfg.history_dir)
    save_snapshot(snap, args.output)
    print(f"Snapshot saved to {args.output} (captured_at={snap.captured_at})")
    return 0


def cmd_diff(args: argparse.Namespace) -> int:
    prev = load_snapshot(args.previous)
    curr = load_snapshot(args.current)
    if prev is None:
        print(f"ERROR: cannot load previous snapshot: {args.previous}", file=sys.stderr)
        return 1
    if curr is None:
        print(f"ERROR: cannot load current snapshot: {args.current}", file=sys.stderr)
        return 1
    changes = diff_snapshots(prev, curr)
    if not changes:
        print("No changes detected between snapshots.")
        return 0
    print(f"Changes detected in {len(changes)} job(s):")
    for job_name, delta in changes.items():
        print(f"  {job_name}:")
        for field, info in delta.items():
            if field == "new":
                print("    (new job)")
            else:
                print(f"    {field}: {info['from']} -> {info['to']}")
    return 0


def cmd_show(args: argparse.Namespace) -> int:
    snap = load_snapshot(args.snapshot)
    if snap is None:
        print(f"ERROR: snapshot not found: {args.snapshot}", file=sys.stderr)
        return 1
    print(f"Snapshot captured at: {snap.captured_at}")
    print(f"{'Job':<30} {'Last Seen':<35} {'Success Rate':>13} {'Consec Fails':>13}")
    print("-" * 95)
    for j in snap.jobs:
        last = j.last_seen or "never"
        print(f"{j.job_name:<30} {last:<35} {j.success_rate:>13.1%} {j.consecutive_failures:>13}")
    return 0


def main() -> None:
    parser = _build_parser()
    args = parser.parse_args()
    dispatch = {"capture": cmd_capture, "diff": cmd_diff, "show": cmd_show}
    sys.exit(dispatch[args.command](args))


if __name__ == "__main__":
    main()
