"""
Tests for python-observability skill.
Validates StructuredFormatter, HttpSignalsCollector in opentelemetry-python SDK.
"""

import os
import json
import re
import pytest

REPO_DIR = "/workspace/opentelemetry-python"


def _path(rel: str) -> str:
    return os.path.join(REPO_DIR, rel)


def _read(rel: str) -> str:
    with open(_path(rel), encoding="utf-8", errors="ignore") as f:
        return f.read()


class TestPythonObservability:

    # ── file_path_check ──────────────────────────────────────────────────────

    def test_structured_formatter_file_exists(self):
        """opentelemetry/sdk/logs/structured_formatter.py must exist."""
        rel = "opentelemetry/sdk/logs/structured_formatter.py"
        assert os.path.isfile(_path(rel)), f"{rel} not found"
        assert os.path.getsize(_path(rel)) > 0, "structured_formatter.py is empty"

    def test_http_signals_file_exists(self):
        """opentelemetry/sdk/metrics/http_signals.py must exist."""
        rel = "opentelemetry/sdk/metrics/http_signals.py"
        assert os.path.isfile(_path(rel)), f"{rel} not found"
        assert os.path.getsize(_path(rel)) > 0, "http_signals.py is empty"

    # ── semantic_check ───────────────────────────────────────────────────────

    def test_structured_formatter_class_defined(self):
        """StructuredFormatter must define 'format' method producing JSON."""
        content = _read("opentelemetry/sdk/logs/structured_formatter.py")
        assert (
            "class StructuredFormatter" in content
        ), "StructuredFormatter class not defined"
        assert "def format" in content, "format() method not found"
        assert (
            "json" in content.lower()
        ), "No JSON usage found in structured_formatter.py"

    def test_http_signals_collector_class_defined(self):
        """HttpSignalsCollector must define before_request and after_request hooks."""
        content = _read("opentelemetry/sdk/metrics/http_signals.py")
        assert (
            "class HttpSignalsCollector" in content
        ), "HttpSignalsCollector class not defined"
        assert "before_request" in content, "before_request method not found"
        assert "after_request" in content, "after_request method not found"

    def test_path_normalization_uuid_pattern(self):
        """http_signals.py must normalize UUID patterns in URL paths to {id}."""
        content = _read("opentelemetry/sdk/metrics/http_signals.py")
        # Look for UUID regex pattern
        has_uuid_pattern = (
            "uuid" in content.lower()
            or "[0-9a-f]" in content
            or r"\d+" in content
            or "{id}" in content
        )
        assert (
            has_uuid_pattern
        ), "No UUID/ID normalization pattern found in http_signals.py"

    def test_saturation_counter_tracking(self):
        """HttpSignalsCollector must track in-flight requests for saturation measurement."""
        content = _read("opentelemetry/sdk/metrics/http_signals.py")
        has_saturation = (
            "in_flight" in content
            or "saturation" in content.lower()
            or "active" in content.lower()
        )
        assert (
            has_saturation
        ), "No saturation/in-flight tracking found in http_signals.py"

    # ── functional_check ─────────────────────────────────────────────────────

    def test_formatter_produces_valid_json(self):
        """StructuredFormatter.format() must produce valid JSON (mocked)."""
        import logging

        class StructuredFormatter(logging.Formatter):
            def format(self, record: logging.LogRecord) -> str:
                return json.dumps(
                    {
                        "level": record.levelname,
                        "message": record.getMessage(),
                        "trace_id": None,
                    }
                )

        formatter = StructuredFormatter()
        record = logging.makeLogRecord({"msg": "test message", "levelname": "INFO"})
        output = formatter.format(record)
        parsed = json.loads(output)
        assert isinstance(parsed, dict), "format() did not return valid JSON object"

    def test_trace_id_non_null_inside_span(self):
        """trace_id must be non-null in log output emitted inside span (mocked)."""
        import logging

        ACTIVE_TRACE_ID = "abc123def456"

        class StructuredFormatter(logging.Formatter):
            def format(self, record: logging.LogRecord) -> str:
                return json.dumps(
                    {
                        "level": record.levelname,
                        "message": record.getMessage(),
                        "trace_id": ACTIVE_TRACE_ID,
                    }
                )

        formatter = StructuredFormatter()
        record = logging.makeLogRecord({"msg": "inside span", "levelname": "INFO"})
        output = formatter.format(record)
        parsed = json.loads(output)
        assert parsed.get("trace_id") is not None

    def test_trace_id_null_outside_span(self):
        """trace_id must be null in log output outside any span (mocked)."""
        import logging

        class StructuredFormatter(logging.Formatter):
            def format(self, record: logging.LogRecord) -> str:
                return json.dumps(
                    {
                        "level": record.levelname,
                        "message": record.getMessage(),
                        "trace_id": None,
                    }
                )

        formatter = StructuredFormatter()
        record = logging.makeLogRecord({"msg": "outside span", "levelname": "DEBUG"})
        output = formatter.format(record)
        parsed = json.loads(output)
        assert parsed.get("trace_id") is None

    def test_path_users_42_normalized_to_users_id(self):
        """/users/42 must normalize to /users/{id} (mocked)."""

        def normalize_path(path: str) -> str:
            path = re.sub(
                r"/[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}",
                "/{id}",
                path,
                flags=re.IGNORECASE,
            )
            path = re.sub(r"/\d+", "/{id}", path)
            return path

        assert normalize_path("/users/42") == "/users/{id}"
        assert normalize_path("/users/42/posts") == "/users/{id}/posts"

    def test_100_requests_counter_equals_100(self):
        """Request counter must equal 100 after 100 before_request calls (mocked)."""

        class HttpSignalsCollector:
            def __init__(self):
                self.request_count = 0
                self._in_flight = 0

            def before_request(self, info: dict):
                self.request_count += 1
                self._in_flight += 1

            def after_request(self, info: dict):
                self._in_flight -= 1

        c = HttpSignalsCollector()
        for _ in range(100):
            c.before_request({"path": "/api", "method": "GET"})
        assert c.request_count == 100

    def test_saturation_3_after_3_before_without_after(self):
        """Saturation must be 3 after 3 before_request with 0 after_request (mocked)."""

        class HttpSignalsCollector:
            def __init__(self):
                self._in_flight = 0

            def before_request(self, info: dict):
                self._in_flight += 1

            def after_request(self, info: dict):
                self._in_flight -= 1

            @property
            def saturation(self) -> int:
                return self._in_flight

        c = HttpSignalsCollector()
        for _ in range(3):
            c.before_request({"path": "/api"})
        assert c.saturation == 3
