"""CLI entry point to start the cronwatch healthcheck HTTP server."""

from __future__ import annotations

import argparse
import signal
import sys
import time

from cronwatch.config import load_config
from cronwatch.digest import DigestReport, build_digest
from cronwatch.healthcheck import HealthcheckServer


def _build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        prog="cronwatch-healthcheck",
        description="Start a lightweight HTTP healthcheck server for cronwatch.",
    )
    p.add_argument("--config", required=True, help="Path to cronwatch config JSON file.")
    p.add_argument("--state-dir", required=True, help="Path to state directory.")
    p.add_argument("--history-dir", required=True, help="Path to history directory.")
    p.add_argument("--host", default="127.0.0.1", help="Bind host (default: 127.0.0.1).")
    p.add_argument("--port", type=int, default=8765, help="Bind port (default: 8765).")
    return p


def cmd_serve(args: argparse.Namespace) -> int:
    cfg = load_config(args.config)

    def get_report() -> DigestReport:
        return build_digest(cfg, state_dir=args.state_dir, history_dir=args.history_dir)

    server = HealthcheckServer(get_report, host=args.host, port=args.port)
    server.start()
    print(f"cronwatch healthcheck listening on {server.address}", flush=True)

    stop = False

    def _handle_signal(signum, frame):  # noqa: ANN001
        nonlocal stop
        stop = True

    signal.signal(signal.SIGTERM, _handle_signal)
    signal.signal(signal.SIGINT, _handle_signal)

    try:
        while not stop:
            time.sleep(1)
    finally:
        server.stop()
        print("cronwatch healthcheck stopped.", flush=True)

    return 0


def main() -> None:
    parser = _build_parser()
    args = parser.parse_args()
    sys.exit(cmd_serve(args))


if __name__ == "__main__":
    main()
