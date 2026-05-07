"""CLI entry-point for the cronwatch dashboard command."""

from __future__ import annotations

import argparse
import sys

from cronwatch.config import load_config
from cronwatch.dashboard import build_dashboard, render_text


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="cronwatch-dashboard",
        description="Print a status dashboard for all configured cron jobs.",
    )
    parser.add_argument("--config", required=True, help="Path to cronwatch config JSON file.")
    parser.add_argument(
        "--state-dir",
        default="/var/lib/cronwatch/state",
        help="Directory where job state files are stored.",
    )
    parser.add_argument(
        "--history-dir",
        default="/var/lib/cronwatch/history",
        help="Directory where job history files are stored.",
    )
    parser.add_argument(
        "--format",
        choices=["text"],
        default="text",
        help="Output format (currently only 'text' is supported).",
    )
    return parser


def cmd_dashboard(args: argparse.Namespace) -> int:
    try:
        cfg = load_config(args.config)
    except (FileNotFoundError, ValueError) as exc:
        print(f"Error loading config: {exc}", file=sys.stderr)
        return 2

    rows = build_dashboard(cfg, args.state_dir, args.history_dir)

    if args.format == "text":
        print(render_text(rows), end="")

    failing = sum(1 for r in rows if r.status == "FAILING")
    missing = sum(1 for r in rows if r.status == "MISSING")

    if failing or missing:
        return 1
    return 0


def main() -> None:  # pragma: no cover
    parser = _build_parser()
    args = parser.parse_args()
    sys.exit(cmd_dashboard(args))


if __name__ == "__main__":  # pragma: no cover
    main()
