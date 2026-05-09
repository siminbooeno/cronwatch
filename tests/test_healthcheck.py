"""Tests for cronwatch.healthcheck."""

from __future__ import annotations

import json
from unittest.mock import MagicMock

import pytest

from cronwatch.digest import DigestReport, JobSummary
from cronwatch.healthcheck import HealthcheckServer, _make_handler
from http.server import HTTPServer


def _make_summary(name: str, consecutive_failures: int = 0, success_rate: float = 1.0) -> JobSummary:
    s = MagicMock(spec=JobSummary)
    s.job_name = name
    s.consecutive_failures = consecutive_failures
    s.success_rate = success_rate
    return s


def _make_report(summaries: list[JobSummary]) -> DigestReport:
    report = MagicMock(spec=DigestReport)
    report.jobs = summaries
    report.healthy_count.return_value = sum(1 for s in summaries if s.consecutive_failures == 0)
    report.unhealthy_count.return_value = sum(1 for s in summaries if s.consecutive_failures > 0)
    return report


class FakeRequest:
    def makefile(self, *args, **kwargs):
        return MagicMock()


def _call_handler(path: str, get_report):
    """Invoke the handler directly and capture the response."""
    handler_cls = _make_handler(get_report)
    written = []

    class FakeWFile:
        def write(self, data):
            written.append(data)

    handler = handler_cls.__new__(handler_cls)
    handler.path = path
    handler.wfile = FakeWFile()
    responses = []

    def fake_send_response(code):
        responses.append(code)

    headers = {}

    def fake_send_header(k, v):
        headers[k] = v

    handler.send_response = fake_send_response
    handler.send_header = fake_send_header
    handler.end_headers = lambda: None
    handler.do_GET()
    return responses, headers, written


def test_health_ok_when_no_unhealthy():
    report = _make_report([_make_summary("job-a"), _make_summary("job-b")])
    codes, headers, written = _call_handler("/health", lambda: report)
    assert codes == [200]
    payload = json.loads(written[0])
    assert payload["status"] == "ok"
    assert payload["healthy"] == 2
    assert payload["unhealthy"] == 0


def test_health_degraded_when_failures():
    report = _make_report([_make_summary("job-a", consecutive_failures=3), _make_summary("job-b")])
    codes, headers, written = _call_handler("/health", lambda: report)
    assert codes == [503]
    payload = json.loads(written[0])
    assert payload["status"] == "degraded"
    assert payload["unhealthy"] == 1


def test_unknown_path_returns_404():
    report = _make_report([])
    codes, _, written = _call_handler("/metrics", lambda: report)
    assert codes == [404]
    assert written == []


def test_content_type_header():
    report = _make_report([])
    _, headers, _ = _call_handler("/health", lambda: report)
    assert headers.get("Content-Type") == "application/json"


def test_server_start_stop():
    report = _make_report([])
    server = HealthcheckServer(lambda: report, host="127.0.0.1", port=19876)
    server.start()
    assert server._server is not None
    assert "19876" in server.address
    server.stop()
    assert server._server is None
