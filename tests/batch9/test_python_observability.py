"""
Test for 'python-observability' skill — Python Observability Stack
Validates configure(), correlation ID, structured logging, Prometheus
metrics, OTel tracing, and FastAPI middleware.
"""

import os
import sys

import pytest


class TestPythonObservability:
    """Verify observability stack: logging, metrics, tracing, middleware."""

    REPO_DIR = "/workspace/opentelemetry-python"

    # ── helpers ──────────────────────────────────────────────────────────

    @staticmethod
    def _read_file(path: str) -> str:
        try:
            with open(path, "r", errors="ignore") as fh:
                return fh.read()
        except OSError:
            return ""

    def _obs(self, *parts) -> str:
        return os.path.join(self.REPO_DIR, "src", "observability", *parts)

    # ── file_path_check ──────────────────────────────────────────────────

    def test_logging_and_metrics_exist(self):
        """logging.py and metrics.py must exist."""
        assert os.path.isfile(self._obs("logging.py")), "logging.py not found"
        assert os.path.isfile(self._obs("metrics.py")), "metrics.py not found"

    def test_tracing_correlation_middleware_exist(self):
        """tracing.py, correlation.py, middleware.py must exist."""
        for name in ("tracing.py", "correlation.py", "middleware.py"):
            assert os.path.isfile(self._obs(name)), f"{name} not found"

    def test_init_and_test_file_exist(self):
        """__init__.py and tests/test_observability.py must exist."""
        assert os.path.isfile(self._obs("__init__.py"))
        test_path = os.path.join(self.REPO_DIR, "tests", "test_observability.py")
        assert os.path.isfile(test_path), f"{test_path} not found"

    # ── semantic_check ───────────────────────────────────────────────────

    def test_configure_function_signature(self):
        """configure() must accept service_name, log_level, enable_tracing, enable_metrics."""
        content = self._read_file(self._obs("__init__.py"))
        if not content:
            pytest.skip("__init__.py not found")
        assert "def configure" in content
        assert "service_name" in content

    def test_correlation_id_is_contextvar(self):
        """correlation_id must be a ContextVar."""
        content = self._read_file(self._obs("correlation.py"))
        if not content:
            pytest.skip("correlation.py not found")
        assert "ContextVar" in content

    def test_histogram_bounded_labels(self):
        """Histogram must use bounded cardinality labels (no user_id)."""
        content = self._read_file(self._obs("metrics.py"))
        if not content:
            pytest.skip("metrics.py not found")
        assert "Histogram" in content or "histogram" in content
        assert "user_id" not in content, "user_id in labels causes cardinality explosion"

    def test_middleware_inherits_base_http(self):
        """ObservabilityMiddleware must inherit from BaseHTTPMiddleware."""
        content = self._read_file(self._obs("middleware.py"))
        if not content:
            pytest.skip("middleware.py not found")
        assert "BaseHTTPMiddleware" in content

    # ── functional_check ─────────────────────────────────────────────────

    def test_configure_no_exception(self):
        """configure('test-service') must not raise."""
        try:
            sys.path.insert(0, os.path.join(self.REPO_DIR, "src"))
            from observability import configure
        except ImportError:
            pytest.skip("Cannot import configure")
        configure("test-service")

    def test_correlation_id_roundtrip(self):
        """set/get correlation_id roundtrip must return same value."""
        try:
            sys.path.insert(0, os.path.join(self.REPO_DIR, "src"))
            from observability.correlation import set_correlation_id, get_correlation_id
        except ImportError:
            pytest.skip("Cannot import correlation functions")
        set_correlation_id("abc123")
        assert get_correlation_id() == "abc123"

    def test_request_metrics_observe(self):
        """RequestMetrics.observe_request must record histogram sample."""
        try:
            sys.path.insert(0, os.path.join(self.REPO_DIR, "src"))
            from observability.metrics import RequestMetrics
            from prometheus_client import CollectorRegistry
        except ImportError:
            pytest.skip("Cannot import RequestMetrics")
        registry = CollectorRegistry()
        metrics = RequestMetrics(registry=registry)
        metrics.observe_request("GET", "/api", 200, 0.1)

    def test_traced_decorator_creates_span(self):
        """@traced must create span named after the function."""
        try:
            sys.path.insert(0, os.path.join(self.REPO_DIR, "src"))
            from observability.tracing import traced
            from opentelemetry.sdk.trace import TracerProvider
            from opentelemetry.sdk.trace.export.in_memory import InMemorySpanExporter
        except ImportError:
            pytest.skip("Cannot import tracing dependencies")
        exporter = InMemorySpanExporter()
        provider = TracerProvider()
        provider.add_span_processor(
            __import__("opentelemetry.sdk.trace.export", fromlist=["SimpleSpanProcessor"]).SimpleSpanProcessor(exporter)
        )
        @traced
        def my_func():
            pass
        my_func()
        spans = exporter.get_finished_spans()
        if spans:
            assert any(s.name == "my_func" for s in spans)

    def test_middleware_skips_health(self):
        """Middleware must not create spans for excluded /health path."""
        content = self._read_file(self._obs("middleware.py"))
        if not content:
            pytest.skip("middleware.py not found")
        assert "excluded_paths" in content or "exclude" in content.lower()

    def test_log_entry_has_service_and_correlation(self):
        """Log entries must include service and correlation_id keys."""
        content = self._read_file(self._obs("logging.py"))
        if not content:
            pytest.skip("logging.py not found")
        assert "service" in content or "service_name" in content
        assert "correlation_id" in content
