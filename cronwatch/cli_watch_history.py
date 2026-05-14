"""CLI for browsing per-job execution history."""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

from cronwatch.history import JobHistory


def _build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        prog="cronwatch-history",
        description="Browse execution history for a cron job.",
    )
    p.add_argument("job", help="Job name")
    p.add_argument(
        "--history-dir",
        default=".cronwatch/history",
        metavar="DIR",
        help="Directory where history files are stored (default: .cronwatch/history)",
    )
    p.add_argument(
        "--limit",
        type=int,
        default=20,
        metavar="N",
        help="Maximum number of records to show (default: 20)",
    )
    p.add_argument(
        "--failures-only",
        action="store_true",
        help="Show only failed executions",
    )
    p.add_argument(
        "--json",
        action="store_true",
        dest="as_json",
        help="Output records as JSON lines",
    )
    return p


def cmd_show(args: argparse.Namespace, out=sys.stdout) -> int:
    history_dir = Path(args.history_dir)
    jh = JobHistory(job_name=args.job, history_dir=history_dir)
    records = jh.records()

    if args.failures_only:
        records = [r for r in records if not r.success]

    records = records[-args.limit :]

    if not records:
        out.write(f"No history found for job '{args.job}'.\n")
        return 0

    if args.as_json:
        import json
        for r in records:
            out.write(
                json.dumps(
                    {
                        "timestamp": r.timestamp,
                        "success": r.success,
                        "exit_code": r.exit_code,
                        "duration_s": r.duration_s,
                        "note": r.note,
                    }
                )
                + "\n"
            )
    else:
        out.write(f"{'Timestamp':<28} {'Status':<8} {'Exit':>4}  {'Duration':>10}\n")
        out.write("-" * 58 + "\n")
        for r in records:
            status = "OK" if r.success else "FAIL"
            dur = f"{r.duration_s:.2f}s" if r.duration_s is not None else "n/a"
            code = str(r.exit_code) if r.exit_code is not None else "n/a"
            out.write(f"{r.timestamp:<28} {status:<8} {code:>4}  {dur:>10}\n")

    rate = jh.success_rate()
    out.write(f"\nSuccess rate (all time): {rate * 100:.1f}%\n")
    return 0


def main(argv=None) -> None:
    parser = _build_parser()
    args = parser.parse_args(argv)
    sys.exit(cmd_show(args))


if __name__ == "__main__":  # pragma: no cover
    main()
