"""CLI sub-commands for managing per-job notes."""
from __future__ import annotations

import argparse
import sys

from cronwatch.job_notes import add_note, get_notes, delete_note, clear_notes


def _build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        prog="cronwatch-notes",
        description="Manage freeform notes attached to cron jobs.",
    )
    p.add_argument("--state-dir", default="/var/lib/cronwatch", help="State directory")
    sub = p.add_subparsers(dest="command", required=True)

    add_p = sub.add_parser("add", help="Add a note to a job")
    add_p.add_argument("job", help="Job name")
    add_p.add_argument("text", help="Note text")
    add_p.add_argument("--author", default=None, help="Author name")

    list_p = sub.add_parser("list", help="List notes for a job")
    list_p.add_argument("job", help="Job name")

    del_p = sub.add_parser("delete", help="Delete a note by ID")
    del_p.add_argument("job", help="Job name")
    del_p.add_argument("id", help="Note ID")

    clr_p = sub.add_parser("clear", help="Remove all notes for a job")
    clr_p.add_argument("job", help="Job name")

    return p


def cmd_add(args: argparse.Namespace) -> int:
    record = add_note(args.state_dir, args.job, args.text, author=args.author)
    print(f"Added note {record['id']} to job '{args.job}'")
    return 0


def cmd_list(args: argparse.Namespace) -> int:
    notes = get_notes(args.state_dir, args.job)
    if not notes:
        print(f"No notes for job '{args.job}'.")
        return 0
    for n in notes:
        author_str = f" [{n['author']}]" if n["author"] else ""
        print(f"{n['id'][:8]}  {n['created_at']}{author_str}  {n['text']}")
    return 0


def cmd_delete(args: argparse.Namespace) -> int:
    removed = delete_note(args.state_dir, args.job, args.id)
    if removed:
        print(f"Deleted note {args.id}.")
        return 0
    print(f"Note {args.id} not found for job '{args.job}'.", file=sys.stderr)
    return 1


def cmd_clear(args: argparse.Namespace) -> int:
    count = clear_notes(args.state_dir, args.job)
    print(f"Cleared {count} note(s) for job '{args.job}'.")
    return 0


def main(argv=None) -> None:
    parser = _build_parser()
    args = parser.parse_args(argv)
    dispatch = {"add": cmd_add, "list": cmd_list, "delete": cmd_delete, "clear": cmd_clear}
    sys.exit(dispatch[args.command](args))


if __name__ == "__main__":
    main()
