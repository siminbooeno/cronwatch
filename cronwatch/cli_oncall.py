"""CLI for managing on-call schedules."""

from __future__ import annotations

import argparse
import sys

from cronwatch.oncall import (
    get_oncall_contacts,
    list_oncall,
    remove_oncall,
    set_oncall,
)


def _build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(prog="cronwatch-oncall",
                                description="Manage on-call contact schedules")
    p.add_argument("--state-dir", default=".cronwatch", metavar="DIR")
    sub = p.add_subparsers(dest="cmd", required=True)

    s = sub.add_parser("set", help="Add or replace an on-call contact")
    s.add_argument("contact", help="Email or webhook URL")
    s.add_argument("--jobs", nargs="*", default=[], metavar="JOB")
    s.add_argument("--tags", nargs="*", default=[], metavar="TAG")
    s.add_argument("--note", default="")

    r = sub.add_parser("remove", help="Remove an on-call contact")
    r.add_argument("contact")

    ls = sub.add_parser("list", help="List all on-call entries")
    ls.add_argument("--json", dest="as_json", action="store_true")

    q = sub.add_parser("query", help="Show contacts for a specific job")
    q.add_argument("job", help="Job name")
    q.add_argument("--tags", nargs="*", default=[], metavar="TAG")

    return p


def cmd_set(args: argparse.Namespace) -> int:
    entry = set_oncall(args.state_dir, args.contact,
                       jobs=args.jobs, tags=args.tags, note=args.note)
    print(f"Set on-call contact: {entry.contact}")
    if entry.jobs:
        print(f"  jobs : {', '.join(entry.jobs)}")
    if entry.tags:
        print(f"  tags : {', '.join(entry.tags)}")
    if entry.note:
        print(f"  note : {entry.note}")
    return 0


def cmd_remove(args: argparse.Namespace) -> int:
    if remove_oncall(args.state_dir, args.contact):
        print(f"Removed on-call contact: {args.contact}")
        return 0
    print(f"No on-call entry found for: {args.contact}", file=sys.stderr)
    return 1


def cmd_list(args: argparse.Namespace) -> int:
    entries = list_oncall(args.state_dir)
    if not entries:
        print("No on-call entries configured.")
        return 0
    if getattr(args, "as_json", False):
        import json
        print(json.dumps([e.__dict__ for e in entries], indent=2))
    else:
        for e in entries:
            scope = "(all jobs)"
            if e.jobs:
                scope = "jobs: " + ", ".join(e.jobs)
            elif e.tags:
                scope = "tags: " + ", ".join(e.tags)
            note = f"  [{e.note}]" if e.note else ""
            print(f"  {e.contact}  {scope}{note}")
    return 0


def cmd_query(args: argparse.Namespace) -> int:
    contacts = get_oncall_contacts(args.state_dir, args.job,
                                   job_tags=args.tags)
    if not contacts:
        print(f"No on-call contacts for job '{args.job}'.")
        return 0
    print(f"On-call contacts for '{args.job}':")
    for c in contacts:
        print(f"  {c}")
    return 0


def main(argv=None) -> None:
    parser = _build_parser()
    args = parser.parse_args(argv)
    dispatch = {"set": cmd_set, "remove": cmd_remove,
                "list": cmd_list, "query": cmd_query}
    sys.exit(dispatch[args.cmd](args))


if __name__ == "__main__":
    main()
