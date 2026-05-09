"""Healthcheck endpoint support for cronwatch.

Exposes a simple HTTP server that responds to GET /health with a JSON
summary of overall system health, suitable for uptime monitors.
"""

from __future__ import annotations

import json
import threading
from http.server import BaseHTTPRequestHandler, HTTPServer
from typing import Callable

from cronwatch.digest import DigestReport


def _make_handler(get_report: Callable[[], DigestReport]) -> type:
    """Return a request handler class bound to the given report factory."""

    class HealthHandler(BaseHTTPRequestHandler):
        def do_GET(self) -> None:  # noqa: N802
            if self.path not in ("/health", "/health/"):
                self.send_response(404)
                self.end_headers()
                return

            report = get_report()
            total = len(report.jobs)
            unhealthy = report.unhealthy_count()
            healthy = report.healthy_count()
            status = "ok" if unhealthy == 0 else "degraded"

            payload = {
                "status": status,
                "total_jobs": total,
                "healthy": healthy,
                "unhealthy": unhealthy,
            }
            body = json.dumps(payload).encode()
            http_code = 200 if status == "ok" else 503

            self.send_response(http_code)
            self.send_header("Content-Type", "application/json")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)

        def log_message(self, fmt: str, *args: object) -> None:  # noqa: D102
            pass  # suppress default stderr logging

    return HealthHandler


class HealthcheckServer:
    """Runs a lightweight HTTP healthcheck server in a background thread."""

    def __init__(self, get_report: Callable[[], DigestReport], host: str = "127.0.0.1", port: int = 8765) -> None:
        self._get_report = get_report
        self._host = host
        self._port = port
        self._server: HTTPServer | None = None
        self._thread: threading.Thread | None = None

    def start(self) -> None:
        handler_cls = _make_handler(self._get_report)
        self._server = HTTPServer((self._host, self._port), handler_cls)
        self._thread = threading.Thread(target=self._server.serve_forever, daemon=True)
        self._thread.start()

    def stop(self) -> None:
        if self._server is not None:
            self._server.shutdown()
            self._server = None

    @property
    def address(self) -> str:
        return f"http://{self._host}:{self._port}/health"
