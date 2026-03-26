"""
Test for 'python-observability' skill — End-to-End Observability Demo
Validates that the Agent created an OpenTelemetry demo script with tracing,
context propagation, and proper trace_id formatting.
"""

import os
import re
import subprocess
import pytest


class TestPythonObservability:
    """Verify OpenTelemetry observability demo implementation."""

    REPO_DIR = "/workspace/opentelemetry-python"

    # ------------------------------------------------------------------
    # L1: file existence & syntax
    # ------------------------------------------------------------------

    def test_demo_script_exists(self):
        """docs/examples/observability_demo.py must exist."""
        fpath = os.path.join(self.REPO_DIR, "docs", "examples", "observability_demo.py")
        assert os.path.isfile(fpath), "observability_demo.py not found"

    def test_demo_script_compiles(self):
        """Demo script must compile without syntax errors."""
        result = subprocess.run(
            ["python", "-m", "py_compile", "docs/examples/observability_demo.py"],
            cwd=self.REPO_DIR,
            capture_output=True,
            text=True,
            timeout=30,
        )
        assert result.returncode == 0, f"Syntax error:\n{result.stderr}"

    # ------------------------------------------------------------------
    # L2: structural checks
    # ------------------------------------------------------------------

    def _read_source(self):
        fpath = os.path.join(self.REPO_DIR, "docs", "examples", "observability_demo.py")
        with open(fpath, "r", encoding="utf-8") as f:
            return f.read()

    def test_tracer_provider_configured(self):
        """Script must configure TracerProvider."""
        source = self._read_source()
        assert "TracerProvider" in source, "TracerProvider not configured"

    def test_console_exporter_used(self):
        """Script must use ConsoleSpanExporter."""
        source = self._read_source()
        assert "ConsoleSpanExporter" in source, "ConsoleSpanExporter not used"

    def test_span_creation(self):
        """Script must create spans (start_as_current_span or start_span)."""
        source = self._read_source()
        patterns = ["start_as_current_span", "start_span"]
        assert any(p in source for p in patterns), "No span creation found"

    def test_context_propagation(self):
        """Script must demonstrate W3C context propagation."""
        source = self._read_source()
        ctx_patterns = [
            "inject",
            "extract",
            "traceparent",
            "TraceContext",
            "propagate",
            "Propagator",
        ]
        found = sum(1 for p in ctx_patterns if p in source)
        assert found >= 2, f"Insufficient context propagation code (matched {found}/6)"

    def test_span_attributes_or_events(self):
        """Script must add attributes or events to spans."""
        source = self._read_source()
        patterns = ["set_attribute", "add_event", "set_status"]
        assert any(
            p in source for p in patterns
        ), "No span attributes/events/status found"

    def test_exception_recording(self):
        """Script must record exceptions with proper span status."""
        source = self._read_source()
        patterns = ["record_exception", "set_status", "StatusCode.ERROR"]
        assert any(
            p in source for p in patterns
        ), "No exception recording / error status handling found"

    # ------------------------------------------------------------------
    # L2: runtime verification
    # ------------------------------------------------------------------

    def test_demo_runs_successfully(self):
        """Demo script must exit with code 0."""
        result = subprocess.run(
            ["python", "docs/examples/observability_demo.py"],
            cwd=self.REPO_DIR,
            capture_output=True,
            text=True,
            timeout=120,
        )
        assert (
            result.returncode == 0
        ), f"Demo failed (rc={result.returncode}):\n{result.stderr[-2000:]}"

    def test_output_contains_trace_id(self):
        """Output must contain a trace_id in 32-char hex format."""
        result = subprocess.run(
            ["python", "docs/examples/observability_demo.py"],
            cwd=self.REPO_DIR,
            capture_output=True,
            text=True,
            timeout=120,
        )
        if result.returncode != 0:
            pytest.skip(f"Demo script failed: {result.stderr[:500]}")
        combined = result.stdout + result.stderr
        # 32-char hex trace_id
        hex32_pattern = re.compile(r"[0-9a-fA-F]{32}")
        assert hex32_pattern.search(
            combined
        ), f"No 32-char hex trace_id found in output:\n{combined[:2000]}"

    def test_output_shows_nested_spans(self):
        """Output should show multiple span names indicating nesting."""
        result = subprocess.run(
            ["python", "docs/examples/observability_demo.py"],
            cwd=self.REPO_DIR,
            capture_output=True,
            text=True,
            timeout=120,
        )
        if result.returncode != 0:
            pytest.skip(f"Demo script failed: {result.stderr[:500]}")
        combined = result.stdout + result.stderr
        # ConsoleSpanExporter outputs span name; count unique "name" occurrences
        span_count = combined.count('"name"') + combined.count("'name'")
        assert (
            span_count >= 2
        ), f"Expected ≥2 spans in output, found {span_count} 'name' fields"
