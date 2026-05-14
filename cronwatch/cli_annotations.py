"""CLI for managing job annotations."""
from __future__ import annotations

import argparse
import json
import sys

from cronwatch.annotations import add_annotation, delete_annotations, get_annotations


def _build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        prog="cronwatch-annotations",
        description="Manage per-job annotations.",
    )
    p.add_argument("--state-dir", default=".cronwatch", metavar="DIR")
    sub = p.add_subparsers(dest="cmd", required=True)

    add = sub.add_parser("add", help="Add an annotation")
    add.add_argument("job", help="Job name")
    add.add_argument("key", help="Annotation key")
    add.add_argument("value", help="Annotation value (stored as string)")
    add.add_argument("--author", default=None, help="Optional author tag")

    ls = sub.add_parser("list", help="List annotations")
    ls.add_argument("job", help="Job name")
    ls.add_argument("--key", default=None, help="Filter by key")
    ls.add_argument("--json", dest="as_json", action="store_true")

    rm = sub.add_parser("delete", help="Delete annotations")
    rm.add_argument("job", help="Job name")
    rm.add_argument("--key", default=None, help="Delete only this key")

    return p


def cmd_add(args: argparse.Namespace) -> int:
    record = add_annotation(
        args.state_dir,
        args.job,
        args.key,
        args.value,
        author=args.author,
    )
    print(f"Added annotation [{record['key']}={record['value']}] at {record['ts']}")
    return 0


def cmd_list(args: argparse.Namespace) -> int:
    records = get_annotations(args.state_dir, args.job, key=args.key)
    if not records:
        print("No annotations found.")
        return 0
    if args.as_json:
        print(json.dumps(records, indent=2))
        return 0
    for r in records:
        author_part = f"  (author: {r['author']})" if "author" in r else ""
        print(f"{r['ts']}  {r['key']}={r['value']}{author_part}")
    return 0


def cmd_delete(args: argparse.Namespace) -> int:
    removed = delete_annotations(args.state_dir, args.job, key=args.key)
    noun = "annotation" if removed == 1 else "annotations"
    print(f"Deleted {removed} {noun}.")
    return 0


def main(argv: list[str] | None = None) -> None:
    parser = _build_parser()
    args = parser.parse_args(argv)
    dispatch = {"add": cmd_add, "list": cmd_list, "delete": cmd_delete}
    sys.exit(dispatch[args.cmd](args))


if __name__ == "__main__":  # pragma: no cover
    main()
