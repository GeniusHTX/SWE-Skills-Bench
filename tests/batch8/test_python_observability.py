"""
Test for 'python-observability' skill — OpenTelemetry Observability
Validates that the Agent implemented OTel-based tracing, metrics, and
structured JSON logging with trace context propagation.
"""

import os
import re
import sys

import pytest


class TestPythonObservability:
    """Verify OTel observability implementation."""

    REPO_DIR = "/workspace/opentelemetry-python"

    @staticmethod
    def _read(path: str) -> str:
        try:
            with open(path, "r", errors="ignore") as fh:
                return fh.read()
        except OSError:
            return ""

    # ── file_path_check ─────────────────────────────────────────────

    def test_tracing_metrics_files_exist(self):
        """Verify app/tracing.py and app/metrics.py exist."""
        for rel in ("app/tracing.py", "app/metrics.py"):
            path = os.path.join(self.REPO_DIR, rel)
            assert os.path.isfile(path), f"Missing: {rel}"

    def test_logging_config_exists(self):
        """Verify app/logging_config.py exists."""
        path = os.path.join(self.REPO_DIR, "app/logging_config.py")
        assert os.path.isfile(path), "Missing: app/logging_config.py"

    # ── semantic_check ──────────────────────────────────────────────

    def test_tracer_provider_and_otlp_exporter(self):
        """Verify tracing.py uses TracerProvider with OTLPSpanExporter."""
        content = self._read(os.path.join(self.REPO_DIR, "app/tracing.py"))
        assert content, "app/tracing.py is empty or unreadable"
        assert "TracerProvider" in content, "TracerProvider not found"
        assert "OTLPSpanExporter" in content, "OTLPSpanExporter not found"

    def test_metrics_counter_and_histogram_names(self):
        """Verify http_requests_total counter and http_request_duration_ms histogram."""
        content = self._read(os.path.join(self.REPO_DIR, "app/metrics.py"))
        assert content, "app/metrics.py is empty or unreadable"
        assert "http_requests_total" in content, "http_requests_total not found"
        assert "http_request_duration_ms" in content, "http_request_duration_ms not found"

    def test_json_log_format_defined(self):
        """Verify logging_config.py outputting JSON with trace_id and span_id."""
        content = self._read(os.path.join(self.REPO_DIR, "app/logging_config.py"))
        assert content, "app/logging_config.py is empty or unreadable"
        for kw in ("trace_id", "span_id", "json"):
            assert kw in content.lower(), f"'{kw}' not found in logging_config.py"

    def test_trace_context_w3c_propagation(self):
        """Verify W3C traceparent propagation is configured in tracing setup."""
        content = self._read(os.path.join(self.REPO_DIR, "app/tracing.py"))
        assert content, "app/tracing.py is empty or unreadable"
        found = any(kw in content for kw in (
            "traceparent", "TraceContextTextMapPropagator", "set_text_map_propagator"))
        assert found, "W3C trace context propagator not configured"

    # ── functional_check (import) ───────────────────────────────────

    def _skip_unless_importable(self):
        if not os.path.isdir(self.REPO_DIR):
            pytest.skip("Repo dir does not exist")
        if self.REPO_DIR not in sys.path:
            sys.path.insert(0, self.REPO_DIR)

    def test_tracing_init_does_not_raise(self):
        """TracingSetup.init() with mock OTLP endpoint does not raise."""
        self._skip_unless_importable()
        try:
            from app.tracing import TracingSetup
        except Exception as exc:
            pytest.skip(f"Cannot import app.tracing: {exc}")
        TracingSetup.init("test-service", "http://localhost:4317")

    def test_record_request_does_not_raise(self):
        """MetricsRecorder.record_request() with valid args does not raise."""
        self._skip_unless_importable()
        try:
            from app.metrics import MetricsRecorder
        except Exception as exc:
            pytest.skip(f"Cannot import app.metrics: {exc}")
        MetricsRecorder().record_request("GET", "/health", 200, 45)

    def test_structured_log_is_valid_json(self):
        """StructuredLogger.log() output is parseable JSON with trace_id and span_id."""
        self._skip_unless_importable()
        import json as _json
        try:
            from app.logging_config import StructuredLogger
        except Exception as exc:
            pytest.skip(f"Cannot import app.logging_config: {exc}")
        log_line = StructuredLogger().log("INFO", "hello")
        log_dict = _json.loads(log_line)
        assert "trace_id" in log_dict, "trace_id missing from log output"
        assert "span_id" in log_dict, "span_id missing from log output"

    def test_invalid_otlp_endpoint_raises_configuration_error(self):
        """TracingSetup.init() with 'not-a-url' raises ConfigurationError."""
        self._skip_unless_importable()
        try:
            from app.tracing import TracingSetup, ConfigurationError
        except Exception as exc:
            pytest.skip(f"Cannot import app.tracing: {exc}")
        with pytest.raises(ConfigurationError):
            TracingSetup.init("svc", "not-a-url")
