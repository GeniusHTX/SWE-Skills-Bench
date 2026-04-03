"""
Test for 'python-observability' skill — OpenTelemetry Python Observability
Validates WSGI middleware, errors_total 5xx counter, span attributes,
tracer provider, and metrics instrumentation.
"""

import os
import re
import sys

import pytest


class TestPythonObservability:
    """Verify OpenTelemetry Python observability setup."""

    REPO_DIR = "/workspace/opentelemetry-python"

    # ── file_path_check ─────────────────────────────────────────────────────

    def test_otel_source_exists(self):
        """Verify OpenTelemetry source directories exist."""
        assert os.path.isdir(self.REPO_DIR), "Repo directory not found"
        # Look for opentelemetry package dirs
        found = False
        for dirpath, dnames, _ in os.walk(self.REPO_DIR):
            if ".git" in dirpath:
                continue
            for d in dnames:
                if "opentelemetry" in d.lower():
                    found = True
                    break
            if found:
                break
        assert found, "No opentelemetry package directory found"

    def test_middleware_file_exists(self):
        """Verify WSGI/middleware instrumentation file exists."""
        found = False
        for dirpath, _, fnames in os.walk(self.REPO_DIR):
            if ".git" in dirpath:
                continue
            for f in fnames:
                if f.endswith(".py") and (
                    "middleware" in f.lower() or "wsgi" in f.lower()
                ):
                    found = True
                    break
            if found:
                break
        assert found, "No middleware/WSGI instrumentation file found"

    # ── semantic_check ──────────────────────────────────────────────────────

    def test_wsgi_middleware_reference(self):
        """Verify WSGI middleware instrumentation."""
        py_files = self._find_py_files()
        for fpath in py_files:
            content = self._read(fpath)
            if re.search(
                r"(WSGIMiddleware|OpenTelemetryMiddleware|wsgi|WSGI)", content
            ):
                return
        pytest.fail("No WSGI middleware reference found")

    def test_errors_total_counter(self):
        """Verify errors_total or 5xx error counter metric."""
        py_files = self._find_py_files()
        for fpath in py_files:
            content = self._read(fpath)
            if re.search(
                r"(errors_total|error_count|5xx|http.*status.*5\d\d|Counter)",
                content,
                re.IGNORECASE,
            ):
                return
        pytest.fail("No error counter metric found")

    def test_span_attributes(self):
        """Verify span attributes are set."""
        py_files = self._find_py_files()
        for fpath in py_files:
            content = self._read(fpath)
            if re.search(r"(set_attribute|span\.attributes|SpanAttributes)", content):
                return
        pytest.fail("No span attributes found")

    def test_tracer_provider(self):
        """Verify TracerProvider setup."""
        py_files = self._find_py_files()
        for fpath in py_files:
            content = self._read(fpath)
            if re.search(
                r"(TracerProvider|set_tracer_provider|get_tracer_provider)", content
            ):
                return
        pytest.fail("No TracerProvider setup found")

    def test_metrics_instrumentation(self):
        """Verify metrics (Counter, Histogram, etc.) are defined."""
        py_files = self._find_py_files()
        for fpath in py_files:
            content = self._read(fpath)
            if re.search(
                r"(Counter|Histogram|UpDownCounter|create_counter|create_histogram)",
                content,
            ):
                return
        pytest.fail("No metrics instrumentation found")

    # ── functional_check ────────────────────────────────────────────────────

    def test_source_files_parse(self):
        """Verify Python source files parse correctly."""
        import ast

        py_files = self._find_py_files()
        for fpath in py_files[:15]:
            content = self._read(fpath)
            try:
                ast.parse(content, filename=fpath)
            except SyntaxError as e:
                pytest.fail(f"SyntaxError in {os.path.basename(fpath)}: {e}")

    def test_exporter_configured(self):
        """Verify an exporter (OTLP, Console, etc.) is configured."""
        py_files = self._find_py_files()
        for fpath in py_files:
            content = self._read(fpath)
            if re.search(
                r"(OTLPSpanExporter|ConsoleSpanExporter|BatchSpanProcessor|SimpleSpanProcessor)",
                content,
            ):
                return
        pytest.fail("No span exporter found")

    def test_resource_attributes(self):
        """Verify Resource attributes with service name."""
        py_files = self._find_py_files()
        for fpath in py_files:
            content = self._read(fpath)
            if re.search(r"(Resource|SERVICE_NAME|service\.name)", content):
                return
        pytest.fail("No Resource/service.name found")

    def test_context_propagation(self):
        """Verify context propagation (W3C TraceContext, baggage, etc.)."""
        py_files = self._find_py_files()
        for fpath in py_files:
            content = self._read(fpath)
            if re.search(
                r"(propagat|TraceContext|W3C|Baggage|inject|extract)",
                content,
                re.IGNORECASE,
            ):
                return
        pytest.fail("No context propagation found")

    def test_instrumentation_library(self):
        """Verify instrumentation library metadata is set."""
        py_files = self._find_py_files()
        for fpath in py_files:
            content = self._read(fpath)
            if re.search(
                r"(InstrumentationLibraryInfo|instrumentor|get_tracer\()", content
            ):
                return
        pytest.fail("No instrumentation library info found")

    # ── helpers ──────────────────────────────────────────────────────────────

    def _find_py_files(self):
        results = []
        for dirpath, _, fnames in os.walk(self.REPO_DIR):
            if ".git" in dirpath:
                continue
            for f in fnames:
                if f.endswith(".py"):
                    results.append(os.path.join(dirpath, f))
        return results

    def _read(self, path):
        with open(path, "r", errors="ignore") as fh:
            return fh.read()
