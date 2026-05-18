"""CLI commands for inspecting job duration trends."""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from cronwatch.config import load_config
from cronwatch.job_trends import compute_all_trends, compute_trend


def _build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        prog="cronwatch-trends",
        description="Show execution duration trends for cron jobs.",
    )
    p.add_argument("--config", required=True, help="Path to config file")
    p.add_argument("--history-dir", required=True, help="Path to history directory")
    sub = p.add_subparsers(dest="command")

    ls = sub.add_parser("list", help="Show trends for all jobs")
    ls.add_argument("--json", dest="as_json", action="store_true")
    ls.add_argument("--limit", type=int, default=50, help="Max records per job")

    show = sub.add_parser("show", help="Show trend for a single job")
    show.add_argument("job", help="Job name")
    show.add_argument("--json", dest="as_json", action="store_true")
    show.add_argument("--limit", type=int, default=50)
    return p


def cmd_list(args) -> int:
    cfg = load_config(args.config)
    history_dir = Path(args.history_dir)
    trends = compute_all_trends(cfg, history_dir, limit=args.limit)
    if args.as_json:
        print(json.dumps([t.as_dict() for t in trends], indent=2))
    else:
        for t in trends:
            print(t.as_text())
    return 0


def cmd_show(args) -> int:
    history_dir = Path(args.history_dir)
    trend = compute_trend(args.job, history_dir, limit=args.limit)
    if args.as_json:
        print(json.dumps(trend.as_dict(), indent=2))
    else:
        print(trend.as_text())
    return 0


def main(argv=None) -> None:
    parser = _build_parser()
    args = parser.parse_args(argv)
    if args.command == "list":
        sys.exit(cmd_list(args))
    elif args.command == "show":
        sys.exit(cmd_show(args))
    else:
        parser.print_help()
        sys.exit(1)


if __name__ == "__main__":
    main()
