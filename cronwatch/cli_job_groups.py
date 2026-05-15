"""CLI for inspecting job groups."""
from __future__ import annotations

import argparse
import sys

from cronwatch.config import load_config
from cronwatch.job_groups import all_group_names, find_group, groups_for_job, jobs_in_group, load_groups


def _build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(prog="cronwatch-groups", description="Inspect job groups")
    p.add_argument("--config", required=True, help="Path to cronwatch config JSON")
    p.add_argument("--groups-file", required=True, help="Path to groups JSON file")
    sub = p.add_subparsers(dest="command")

    sub.add_parser("list", help="List all group names")

    show = sub.add_parser("show", help="Show jobs in a group")
    show.add_argument("group", help="Group name")

    member = sub.add_parser("membership", help="Show groups a job belongs to")
    member.add_argument("job", help="Job name")

    return p


def cmd_list(args: argparse.Namespace) -> int:
    groups = load_groups(args.groups_file)
    names = all_group_names(groups)
    if not names:
        print("No groups defined.")
        return 0
    for name in names:
        print(name)
    return 0


def cmd_show(args: argparse.Namespace) -> int:
    groups = load_groups(args.groups_file)
    group = find_group(groups, args.group)
    if group is None:
        print(f"Group not found: {args.group}", file=sys.stderr)
        return 1
    cfg = load_config(args.config)
    jobs = jobs_in_group(group, cfg)
    if group.description:
        print(f"Group: {group.name}  ({group.description})")
    else:
        print(f"Group: {group.name}")
    if not jobs:
        print("  (no matching jobs in config)")
    for j in jobs:
        print(f"  - {j.name}")
    return 0


def cmd_membership(args: argparse.Namespace) -> int:
    groups = load_groups(args.groups_file)
    matched = groups_for_job(groups, args.job)
    if not matched:
        print(f"{args.job} is not in any group.")
        return 0
    print(f"Groups containing '{args.job}':")
    for g in matched:
        print(f"  - {g.name}")
    return 0


def main(argv: list[str] | None = None) -> None:  # pragma: no cover
    parser = _build_parser()
    args = parser.parse_args(argv)
    dispatch = {"list": cmd_list, "show": cmd_show, "membership": cmd_membership}
    fn = dispatch.get(args.command)
    if fn is None:
        parser.print_help()
        sys.exit(1)
    sys.exit(fn(args))


if __name__ == "__main__":  # pragma: no cover
    main()
