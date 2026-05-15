"""CLI for searching job configurations."""
from __future__ import annotations

import argparse
import json
import sys

from cronwatch.config import load_config
from cronwatch.job_search import find_job_by_name, search_jobs


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="cronwatch-search",
        description="Search job configurations by keyword or name.",
    )
    parser.add_argument("--config", required=True, help="Path to config file")
    sub = parser.add_subparsers(dest="cmd")

    p_search = sub.add_parser("search", help="Full-text search across jobs")
    p_search.add_argument("query", help="Search term")
    p_search.add_argument(
        "--fields",
        nargs="+",
        help="Fields to search (default: name command tags labels)",
    )
    p_search.add_argument("--json", dest="as_json", action="store_true")

    p_find = sub.add_parser("find", help="Find a job by exact name")
    p_find.add_argument("name", help="Job name")
    p_find.add_argument("--json", dest="as_json", action="store_true")

    return parser


def cmd_search(args: argparse.Namespace) -> int:
    config = load_config(args.config)
    results = search_jobs(config, args.query, fields=args.fields)
    if not results:
        print("No jobs matched.")
        return 0
    if args.as_json:
        print(json.dumps([r.as_dict() for r in results], indent=2))
    else:
        for r in results:
            fields = ", ".join(r.matched_fields)
            print(f"  {r.job.name}  (matched: {fields})")
            print(f"    command: {r.job.command}")
    return 0


def cmd_find(args: argparse.Namespace) -> int:
    config = load_config(args.config)
    job = find_job_by_name(config, args.name)
    if job is None:
        print(f"Job '{args.name}' not found.")
        return 1
    if args.as_json:
        print(json.dumps({"name": job.name, "command": job.command}, indent=2))
    else:
        print(f"name:    {job.name}")
        print(f"command: {job.command}")
        if job.tags:
            print(f"tags:    {', '.join(job.tags)}")
    return 0


def main(argv=None) -> int:
    parser = _build_parser()
    args = parser.parse_args(argv)
    if args.cmd == "search":
        return cmd_search(args)
    if args.cmd == "find":
        return cmd_find(args)
    parser.print_help()
    return 1


if __name__ == "__main__":
    sys.exit(main())
