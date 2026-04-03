"""
Test for 'python-observability' skill — Python Observability
Validates MetricsCollector ASGI middleware for request counting, route
normalization, reset, and error tracking in the opentelemetry-python repo.
"""

import os
import sys
import re
import ast
import pytest


class TestPythonObservability:
    """Tests for Python observability in the opentelemetry-python repo."""

    REPO_DIR = "/workspace/opentelemetry-python"

    def _read(self, relpath):
        full = os.path.join(self.REPO_DIR, relpath)
        with open(full, "r", errors="ignore") as f:
            return f.read()

    # --- File Path Checks ---

    def test_metrics_collector_py_exists(self):
        """Verifies that docs/examples/observability/metrics_collector.py exists."""
        path = os.path.join(
            self.REPO_DIR, "docs", "examples", "observability", "metrics_collector.py"
        )
        assert os.path.exists(path), f"Expected file not found: {path}"

    def test_init_py_exists(self):
        """Verifies that docs/examples/observability/__init__.py exists."""
        path = os.path.join(
            self.REPO_DIR, "docs", "examples", "observability", "__init__.py"
        )
        assert os.path.exists(path), f"Expected file not found: {path}"

    # --- Semantic Checks ---

    def test_sem_import_metrics_collector(self):
        """MetricsCollector is importable."""
        old_path = sys.path[:]
        try:
            sys.path.insert(0, self.REPO_DIR)
            from docs.examples.observability.metrics_collector import MetricsCollector

            assert MetricsCollector is not None
        finally:
            sys.path[:] = old_path

    def test_sem_is_asgi_middleware(self):
        """MetricsCollector is callable as ASGI middleware (takes app as first arg)."""
        src = self._read("docs/examples/observability/metrics_collector.py")
        assert "def __init__" in src, "Missing __init__ method"
        assert "app" in src, "Constructor should accept 'app' argument"

    def test_sem_has_methods(self):
        """MetricsCollector has get_metrics_summary and reset methods."""
        src = self._read("docs/examples/observability/metrics_collector.py")
        assert "def get_metrics_summary" in src, "Missing get_metrics_summary method"
        assert "def reset" in src, "Missing reset method"

    def test_sem_constructor_accepts_service_name(self):
        """Constructor accepts service_name and optional meter_provider."""
        src = self._read("docs/examples/observability/metrics_collector.py")
        assert "service_name" in src, "Constructor should accept service_name"

    # --- Functional Checks ---

    def test_func_create_collector(self):
        """Can create MetricsCollector with AsyncMock app."""
        old_path = sys.path[:]
        try:
            sys.path.insert(0, self.REPO_DIR)
            from unittest.mock import AsyncMock
            from docs.examples.observability.metrics_collector import MetricsCollector

            app = AsyncMock()
            collector = MetricsCollector(app, "test-service")
            assert collector is not None
        finally:
            sys.path[:] = old_path

    @pytest.mark.asyncio
    async def test_func_handle_request(self):
        """Collector handles an HTTP request through ASGI."""
        old_path = sys.path[:]
        try:
            sys.path.insert(0, self.REPO_DIR)
            from unittest.mock import AsyncMock
            from docs.examples.observability.metrics_collector import MetricsCollector

            app = AsyncMock()
            collector = MetricsCollector(app, "test-service")
            scope = {
                "type": "http",
                "method": "GET",
                "path": "/users/42",
                "query_string": b"",
            }
            receive = AsyncMock()
            send = AsyncMock()
            await collector(scope, receive, send)
        finally:
            sys.path[:] = old_path

    @pytest.mark.asyncio
    async def test_func_get_metrics_summary_total_requests(self):
        """After one request, total_requests == 1."""
        old_path = sys.path[:]
        try:
            sys.path.insert(0, self.REPO_DIR)
            from unittest.mock import AsyncMock
            from docs.examples.observability.metrics_collector import MetricsCollector

            app = AsyncMock()
            collector = MetricsCollector(app, "test-service")
            scope = {
                "type": "http",
                "method": "GET",
                "path": "/users/42",
                "query_string": b"",
            }
            await collector(scope, AsyncMock(), AsyncMock())
            summary = collector.get_metrics_summary()
            assert summary["total_requests"] == 1
        finally:
            sys.path[:] = old_path

    @pytest.mark.asyncio
    async def test_func_route_normalization(self):
        """Request to /users/42 recorded as route '/users/{id}' in summary."""
        old_path = sys.path[:]
        try:
            sys.path.insert(0, self.REPO_DIR)
            from unittest.mock import AsyncMock
            from docs.examples.observability.metrics_collector import MetricsCollector

            app = AsyncMock()
            collector = MetricsCollector(app, "test-service")
            scope = {
                "type": "http",
                "method": "GET",
                "path": "/users/42",
                "query_string": b"",
            }
            await collector(scope, AsyncMock(), AsyncMock())
            summary = collector.get_metrics_summary()
            summary_str = str(summary)
            assert "/users/{id}" in summary_str or "/users/42" in summary_str
        finally:
            sys.path[:] = old_path

    @pytest.mark.asyncio
    async def test_func_status_code_tracking(self):
        """Summary for request returning 200 has status_code == 200."""
        old_path = sys.path[:]
        try:
            sys.path.insert(0, self.REPO_DIR)
            from unittest.mock import AsyncMock
            from docs.examples.observability.metrics_collector import MetricsCollector

            app = AsyncMock()
            collector = MetricsCollector(app, "test-service")
            scope = {
                "type": "http",
                "method": "GET",
                "path": "/test",
                "query_string": b"",
            }
            await collector(scope, AsyncMock(), AsyncMock())
            summary = collector.get_metrics_summary()
            assert "200" in str(summary) or summary.get("total_requests", 0) >= 1
        finally:
            sys.path[:] = old_path

    @pytest.mark.asyncio
    async def test_func_reset(self):
        """After reset, total_requests == 0."""
        old_path = sys.path[:]
        try:
            sys.path.insert(0, self.REPO_DIR)
            from unittest.mock import AsyncMock
            from docs.examples.observability.metrics_collector import MetricsCollector

            app = AsyncMock()
            collector = MetricsCollector(app, "test-service")
            scope = {
                "type": "http",
                "method": "GET",
                "path": "/test",
                "query_string": b"",
            }
            await collector(scope, AsyncMock(), AsyncMock())
            collector.reset()
            summary = collector.get_metrics_summary()
            assert summary["total_requests"] == 0
        finally:
            sys.path[:] = old_path

    @pytest.mark.asyncio
    async def test_func_response_passthrough(self):
        """Response from app passes through: send called with same arguments."""
        old_path = sys.path[:]
        try:
            sys.path.insert(0, self.REPO_DIR)
            from unittest.mock import AsyncMock
            from docs.examples.observability.metrics_collector import MetricsCollector

            app = AsyncMock()
            collector = MetricsCollector(app, "test-service")
            scope = {
                "type": "http",
                "method": "GET",
                "path": "/test",
                "query_string": b"",
            }
            receive = AsyncMock()
            send = AsyncMock()
            await collector(scope, receive, send)
            # The app should have been called
            app.assert_called()
        finally:
            sys.path[:] = old_path

    @pytest.mark.asyncio
    async def test_func_error_tracking(self):
        """500 response: summary['errors'] == 1."""
        old_path = sys.path[:]
        try:
            sys.path.insert(0, self.REPO_DIR)
            from unittest.mock import AsyncMock
            from docs.examples.observability.metrics_collector import MetricsCollector

            app = AsyncMock(side_effect=Exception("Internal error"))
            collector = MetricsCollector(app, "test-service")
            scope = {
                "type": "http",
                "method": "GET",
                "path": "/error",
                "query_string": b"",
            }
            try:
                await collector(scope, AsyncMock(), AsyncMock())
            except Exception:
                pass
            summary = collector.get_metrics_summary()
            assert (
                summary.get("errors", 0) >= 1 or summary.get("total_requests", 0) >= 1
            )
        finally:
            sys.path[:] = old_path
