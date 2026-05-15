"""CLI for managing per-job environment variable overrides."""
from __future__ import annotations

import argparse
import sys

from cronwatch.job_env import set_var, unset_var, get_env, clear_env


def _build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        prog="cronwatch-env",
        description="Manage per-job environment variable overrides.",
    )
    p.add_argument("--state-dir", default="/var/lib/cronwatch", metavar="DIR")
    sub = p.add_subparsers(dest="command", required=True)

    s = sub.add_parser("set", help="Set a variable for a job")
    s.add_argument("job", help="Job name")
    s.add_argument("key", help="Variable name")
    s.add_argument("value", help="Variable value")

    u = sub.add_parser("unset", help="Remove a variable from a job")
    u.add_argument("job", help="Job name")
    u.add_argument("key", help="Variable name")

    ls = sub.add_parser("list", help="List all variables for a job")
    ls.add_argument("job", help="Job name")

    cl = sub.add_parser("clear", help="Remove all variables for a job")
    cl.add_argument("job", help="Job name")

    return p


def cmd_set(args: argparse.Namespace) -> int:
    set_var(args.state_dir, args.job, args.key, args.value)
    print(f"Set {args.key}={args.value} for job '{args.job}'")
    return 0


def cmd_unset(args: argparse.Namespace) -> int:
    removed = unset_var(args.state_dir, args.job, args.key)
    if removed:
        print(f"Unset {args.key} for job '{args.job}'")
    else:
        print(f"Variable {args.key} not found for job '{args.job}'")
        return 1
    return 0


def cmd_list(args: argparse.Namespace) -> int:
    env = get_env(args.state_dir, args.job)
    if not env:
        print(f"No environment overrides for job '{args.job}'")
        return 0
    for key, value in sorted(env.items()):
        print(f"{key}={value}")
    return 0


def cmd_clear(args: argparse.Namespace) -> int:
    count = clear_env(args.state_dir, args.job)
    print(f"Cleared {count} variable(s) for job '{args.job}'")
    return 0


def main() -> None:
    parser = _build_parser()
    args = parser.parse_args()
    dispatch = {"set": cmd_set, "unset": cmd_unset, "list": cmd_list, "clear": cmd_clear}
    sys.exit(dispatch[args.command](args))


if __name__ == "__main__":
    main()
