"""CLI commands for job ownership management."""
from __future__ import annotations

import argparse
import sys

from cronwatch.job_ownership import (
    set_owner, remove_owner, get_owner, list_owners,
    jobs_owned_by, jobs_owned_by_team,
)


def _build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(prog="cronwatch-ownership", description="Manage job ownership")
    p.add_argument("--state-dir", default=".cronwatch", metavar="DIR")
    sub = p.add_subparsers(dest="cmd", required=True)

    s = sub.add_parser("set", help="Assign an owner to a job")
    s.add_argument("job", help="Job name")
    s.add_argument("owner", help="Owner name")
    s.add_argument("--email", default=None)
    s.add_argument("--team", default=None)

    r = sub.add_parser("remove", help="Remove ownership from a job")
    r.add_argument("job", help="Job name")

    g = sub.add_parser("get", help="Show owner of a job")
    g.add_argument("job", help="Job name")

    sub.add_parser("list", help="List all ownership records")

    by = sub.add_parser("by-owner", help="List jobs owned by a person")
    by.add_argument("owner", help="Owner name")

    bt = sub.add_parser("by-team", help="List jobs owned by a team")
    bt.add_argument("team", help="Team name")

    return p


def cmd_set(args) -> int:
    rec = set_owner(args.state_dir, args.job, args.owner, email=args.email, team=args.team)
    print(f"Owner set: {rec['job']} -> {rec['owner']}" + (f" <{rec['email']}>" if rec['email'] else "") + (f" [{rec['team']}]" if rec['team'] else ""))
    return 0


def cmd_remove(args) -> int:
    if remove_owner(args.state_dir, args.job):
        print(f"Ownership removed for '{args.job}'.")
        return 0
    print(f"No ownership record found for '{args.job}'.", file=sys.stderr)
    return 1


def cmd_get(args) -> int:
    rec = get_owner(args.state_dir, args.job)
    if rec is None:
        print(f"No owner assigned to '{args.job}'.")
        return 1
    print(f"Job:   {rec['job']}")
    print(f"Owner: {rec['owner']}")
    if rec.get("email"):
        print(f"Email: {rec['email']}")
    if rec.get("team"):
        print(f"Team:  {rec['team']}")
    print(f"Since: {rec['assigned_at']}")
    return 0


def _print_records(records) -> None:
    if not records:
        print("(none)")
        return
    for r in records:
        parts = [r["job"], r["owner"]]
        if r.get("email"):
            parts.append(f"<{r['email']}>")
        if r.get("team"):
            parts.append(f"[{r['team']}]")
        print("  " + "  ".join(parts))


def main(argv=None) -> int:
    p = _build_parser()
    args = p.parse_args(argv)
    if args.cmd == "set":
        return cmd_set(args)
    if args.cmd == "remove":
        return cmd_remove(args)
    if args.cmd == "get":
        return cmd_get(args)
    if args.cmd == "list":
        _print_records(list_owners(args.state_dir))
        return 0
    if args.cmd == "by-owner":
        _print_records(jobs_owned_by(args.state_dir, args.owner))
        return 0
    if args.cmd == "by-team":
        _print_records(jobs_owned_by_team(args.state_dir, args.team))
        return 0
    return 1


if __name__ == "__main__":
    sys.exit(main())
