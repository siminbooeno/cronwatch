"""CLI for managing job aliases."""
from __future__ import annotations

import argparse
import sys

from cronwatch.job_aliases import (
    aliases_for_job,
    list_aliases,
    remove_alias,
    resolve_alias,
    set_alias,
)


def _build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(prog="cronwatch-aliases", description="Manage job aliases")
    p.add_argument("--state-dir", default=".cronwatch", metavar="DIR")
    sub = p.add_subparsers(dest="command", required=True)

    s = sub.add_parser("set", help="Create or update an alias")
    s.add_argument("alias")
    s.add_argument("job_name")

    r = sub.add_parser("remove", help="Remove an alias")
    r.add_argument("alias")

    rs = sub.add_parser("resolve", help="Resolve an alias to a job name")
    rs.add_argument("alias")

    sub.add_parser("list", help="List all aliases")

    fj = sub.add_parser("for-job", help="List aliases pointing to a job")
    fj.add_argument("job_name")

    return p


def cmd_set(args: argparse.Namespace) -> int:
    set_alias(args.state_dir, args.alias, args.job_name)
    print(f"Alias '{args.alias}' -> '{args.job_name}' saved.")
    return 0


def cmd_remove(args: argparse.Namespace) -> int:
    if remove_alias(args.state_dir, args.alias):
        print(f"Alias '{args.alias}' removed.")
        return 0
    print(f"Alias '{args.alias}' not found.", file=sys.stderr)
    return 1


def cmd_resolve(args: argparse.Namespace) -> int:
    target = resolve_alias(args.state_dir, args.alias)
    if target is None:
        print(f"No alias '{args.alias}' found.", file=sys.stderr)
        return 1
    print(target)
    return 0


def cmd_list(args: argparse.Namespace) -> int:
    aliases = list_aliases(args.state_dir)
    if not aliases:
        print("No aliases defined.")
        return 0
    for alias, target in sorted(aliases.items()):
        print(f"{alias:30s}  ->  {target}")
    return 0


def cmd_for_job(args: argparse.Namespace) -> int:
    found = aliases_for_job(args.state_dir, args.job_name)
    if not found:
        print(f"No aliases for '{args.job_name}'.")
        return 0
    for a in sorted(found):
        print(a)
    return 0


def main(argv: list[str] | None = None) -> None:
    parser = _build_parser()
    args = parser.parse_args(argv)
    handlers = {
        "set": cmd_set,
        "remove": cmd_remove,
        "resolve": cmd_resolve,
        "list": cmd_list,
        "for-job": cmd_for_job,
    }
    sys.exit(handlers[args.command](args))


if __name__ == "__main__":
    main()
