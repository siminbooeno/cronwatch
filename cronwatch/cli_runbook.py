"""CLI commands for managing runbook links."""

from __future__ import annotations

import argparse
import sys

from cronwatch.runbook import delete_runbook, get_runbook, list_runbooks, set_runbook


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="cronwatch-runbook",
        description="Manage runbook links for cron jobs",
    )
    parser.add_argument("--state-dir", default=".cronwatch", metavar="DIR")
    sub = parser.add_subparsers(dest="command", required=True)

    p_set = sub.add_parser("set", help="Attach a runbook URL to a job")
    p_set.add_argument("job", help="Job name")
    p_set.add_argument("url", help="Runbook URL")

    p_get = sub.add_parser("get", help="Show runbook URL for a job")
    p_get.add_argument("job", help="Job name")

    p_del = sub.add_parser("delete", help="Remove a runbook link")
    p_del.add_argument("job", help="Job name")

    sub.add_parser("list", help="List all runbook links")

    return parser


def cmd_set(args: argparse.Namespace) -> int:
    set_runbook(args.state_dir, args.job, args.url)
    print(f"Runbook set for '{args.job}': {args.url}")
    return 0


def cmd_get(args: argparse.Namespace) -> int:
    url = get_runbook(args.state_dir, args.job)
    if url is None:
        print(f"No runbook configured for '{args.job}'")
        return 1
    print(url)
    return 0


def cmd_delete(args: argparse.Namespace) -> int:
    removed = delete_runbook(args.state_dir, args.job)
    if not removed:
        print(f"No runbook found for '{args.job}'")
        return 1
    print(f"Runbook removed for '{args.job}'")
    return 0


def cmd_list(args: argparse.Namespace) -> int:
    entries = list_runbooks(args.state_dir)
    if not entries:
        print("No runbooks configured.")
        return 0
    width = max(len(e["job"]) for e in entries)
    for e in entries:
        print(f"{e['job']:<{width}}  {e['url']}")
    return 0


def main(argv: list[str] | None = None) -> None:
    parser = _build_parser()
    args = parser.parse_args(argv)
    dispatch = {"set": cmd_set, "get": cmd_get, "delete": cmd_delete, "list": cmd_list}
    sys.exit(dispatch[args.command](args))


if __name__ == "__main__":
    main()
