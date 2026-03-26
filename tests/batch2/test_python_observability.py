"""
Test for 'python-observability' skill — Python Observability Patterns
Validates that the Agent created an OpenTelemetry observability demo script
demonstrating tracing, metrics, and structured logging with trace correlation.
"""

import os
import re
import subprocess

import pytest


class TestPythonObservability:
    """Verify OpenTelemetry observability demo script."""

    REPO_DIR = "/workspace/opentelemetry-python"

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    def _read(self, *parts):
        fpath = os.path.join(self.REPO_DIR, *parts)
        assert os.path.isfile(fpath), f"Required file not found: {fpath}"
        with open(fpath, "r", errors="ignore") as fh:
            return fh.read()

    # ------------------------------------------------------------------
    # L1: File existence and syntax
    # ------------------------------------------------------------------

    def test_demo_file_exists(self):
        """docs/examples/observability_demo.py must exist."""
        fpath = os.path.join(self.REPO_DIR, "docs", "examples", "observability_demo.py")
        assert os.path.isfile(fpath), "docs/examples/observability_demo.py not found"

    def test_demo_compiles(self):
        """observability_demo.py must be syntactically valid Python."""
        result = subprocess.run(
            ["python", "-m", "py_compile", "docs/examples/observability_demo.py"],
            cwd=self.REPO_DIR,
            capture_output=True,
            text=True,
            timeout=30,
        )
        assert (
            result.returncode == 0
        ), f"Syntax error in observability_demo.py:\n{result.stderr}"

    def test_demo_has_main_entry_point(self):
        """Script must have a __main__ entry point."""
        content = self._read("docs", "examples", "observability_demo.py")
        assert re.search(
            r'if\s+__name__\s*==\s*["\']__main__["\']', content
        ), "observability_demo.py missing __main__ entry point"

    # ------------------------------------------------------------------
    # L1: Tracing
    # ------------------------------------------------------------------

    def test_tracer_provider_initialization(self):
        """Script must initialize a TracerProvider."""
        content = self._read("docs", "examples", "observability_demo.py")
        patterns = [
            r"TracerProvider",
            r"tracer_provider",
            r"set_tracer_provider",
        ]
        assert any(
            re.search(p, content) for p in patterns
        ), "Script does not initialize a TracerProvider"

    def test_creates_nested_spans(self):
        """Script must create nested spans simulating a request flow."""
        content = self._read("docs", "examples", "observability_demo.py")
        span_patterns = [
            r"start_as_current_span",
            r"start_span",
            r"tracer\.start",
        ]
        span_calls = sum(len(re.findall(p, content)) for p in span_patterns)
        assert span_calls >= 2, (
            f"Script creates only {span_calls} span(s) — "
            f"need at least 2 for nested spans (e.g., HTTP handler → DB query)"
        )

    def test_span_attributes_set(self):
        """Spans must carry attributes for request metadata."""
        content = self._read("docs", "examples", "observability_demo.py")
        attr_patterns = [
            r"set_attribute",
            r"SpanAttributes",
            r"attributes\s*=",
            r"\.attributes",
        ]
        assert any(
            re.search(p, content) for p in attr_patterns
        ), "Spans do not set attributes for request metadata"

    # ------------------------------------------------------------------
    # L1: Metrics
    # ------------------------------------------------------------------

    def test_meter_provider_initialization(self):
        """Script must initialize a MeterProvider or create a Meter."""
        content = self._read("docs", "examples", "observability_demo.py")
        patterns = [
            r"MeterProvider",
            r"meter_provider",
            r"get_meter",
            r"create_meter",
        ]
        assert any(
            re.search(p, content) for p in patterns
        ), "Script does not initialize a MeterProvider or Meter"

    def test_creates_counter_metric(self):
        """Script must create a counter metric (e.g., request count)."""
        content = self._read("docs", "examples", "observability_demo.py")
        patterns = [
            r"create_counter",
            r"Counter\(",
            r"counter",
            r"\.add\(",
        ]
        assert any(
            re.search(p, content, re.IGNORECASE) for p in patterns
        ), "Script does not create a counter metric"

    def test_creates_histogram_metric(self):
        """Script must create a histogram metric (e.g., request duration)."""
        content = self._read("docs", "examples", "observability_demo.py")
        patterns = [
            r"create_histogram",
            r"Histogram\(",
            r"histogram",
            r"\.record\(",
        ]
        assert any(
            re.search(p, content, re.IGNORECASE) for p in patterns
        ), "Script does not create a histogram metric"

    # ------------------------------------------------------------------
    # L1: Logging with trace correlation
    # ------------------------------------------------------------------

    def test_structured_logging_configured(self):
        """Script must set up structured logging."""
        content = self._read("docs", "examples", "observability_demo.py")
        log_patterns = [
            r"logging",
            r"logger",
            r"getLogger",
            r"LoggingHandler",
            r"structlog",
        ]
        assert any(
            re.search(p, content) for p in log_patterns
        ), "Script does not configure structured logging"

    def test_log_trace_correlation(self):
        """Log output must include trace/span IDs for correlation."""
        content = self._read("docs", "examples", "observability_demo.py")
        correlation_patterns = [
            r"trace_id",
            r"span_id",
            r"otelTraceID",
            r"otelSpanID",
            r"get_current_span",
            r"format_trace_id",
            r"trace.*id.*log|log.*trace.*id",
        ]
        assert any(
            re.search(p, content, re.IGNORECASE) for p in correlation_patterns
        ), "Logging does not include trace/span ID correlation"

    def test_multiple_log_levels(self):
        """Script must log at different severity levels."""
        content = self._read("docs", "examples", "observability_demo.py")
        levels = [
            r"\.info\(",
            r"\.warning\(",
            r"\.error\(",
            r"\.debug\(",
            r"\.warn\(",
            r"\.critical\(",
        ]
        level_count = sum(1 for p in levels if re.search(p, content))
        assert level_count >= 2, (
            f"Script only uses {level_count} log level(s) — "
            f"need at least 2 (e.g., info, warning, error)"
        )

    # ------------------------------------------------------------------
    # L2: Dynamic execution
    # ------------------------------------------------------------------

    def test_demo_runs_successfully(self):
        """observability_demo.py must run to completion."""
        result = subprocess.run(
            ["python", "docs/examples/observability_demo.py"],
            cwd=self.REPO_DIR,
            capture_output=True,
            text=True,
            timeout=60,
        )
        assert result.returncode == 0, (
            f"Demo script failed (rc={result.returncode}):\n"
            f"stderr: {result.stderr[-3000:]}"
        )

    def test_demo_output_contains_trace_data(self):
        """Running the demo must produce output containing trace/span information."""
        result = subprocess.run(
            ["python", "docs/examples/observability_demo.py"],
            cwd=self.REPO_DIR,
            capture_output=True,
            text=True,
            timeout=60,
        )
        combined = result.stdout + result.stderr
        trace_patterns = [
            r"trace",
            r"span",
            r"Span",
            r"Trace",
            r"[0-9a-f]{32}",
            r"StatusCode",
        ]
        assert any(re.search(p, combined, re.IGNORECASE) for p in trace_patterns), (
            f"Demo output does not contain trace/span information:\n"
            f"{combined[:3000]}"
        )
