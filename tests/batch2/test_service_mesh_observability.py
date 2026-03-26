"""
Test for 'service-mesh-observability' skill — Mesh-Wide Metrics Aggregation
Validates that the Agent created mesh-wide metrics aggregation for Linkerd viz
with Go structs, aggregation logic, and HTTP handler.
"""

import os
import re
import subprocess

import pytest


class TestServiceMeshObservability:
    """Verify Linkerd viz mesh-wide metrics aggregation."""

    REPO_DIR = "/workspace/linkerd2"
    METRICS_DIR = "viz/metrics"

    def _read(self, *parts):
        fpath = os.path.join(self.REPO_DIR, *parts)
        assert os.path.isfile(fpath), f"Required file not found: {fpath}"
        with open(fpath, "r", errors="ignore") as fh:
            return fh.read()

    # ------------------------------------------------------------------
    # L1: File existence
    # ------------------------------------------------------------------

    def test_aggregator_go_exists(self):
        """aggregator.go must exist."""
        assert os.path.isfile(
            os.path.join(self.REPO_DIR, self.METRICS_DIR, "aggregator.go")
        )

    def test_types_go_exists(self):
        """types.go must exist."""
        assert os.path.isfile(os.path.join(self.REPO_DIR, self.METRICS_DIR, "types.go"))

    def test_handler_go_exists(self):
        """handler.go must exist."""
        assert os.path.isfile(
            os.path.join(self.REPO_DIR, self.METRICS_DIR, "handler.go")
        )

    # ------------------------------------------------------------------
    # L1: Package declarations
    # ------------------------------------------------------------------

    def test_aggregator_has_package(self):
        """aggregator.go must declare a package."""
        content = self._read(self.METRICS_DIR, "aggregator.go")
        assert re.search(r"^package\s+\w+", content, re.MULTILINE)

    def test_types_has_package(self):
        """types.go must declare a package."""
        content = self._read(self.METRICS_DIR, "types.go")
        assert re.search(r"^package\s+\w+", content, re.MULTILINE)

    def test_handler_has_package(self):
        """handler.go must declare a package."""
        content = self._read(self.METRICS_DIR, "handler.go")
        assert re.search(r"^package\s+\w+", content, re.MULTILINE)

    # ------------------------------------------------------------------
    # L2: Types — Go struct definitions
    # ------------------------------------------------------------------

    def test_service_metrics_struct(self):
        """types.go must define a service-level metrics struct."""
        content = self._read(self.METRICS_DIR, "types.go")
        patterns = [
            r"type\s+ServiceMetrics\s+struct",
            r"type\s+ServiceStats\s+struct",
            r"type\s+\w*Service\w*Metric\w*\s+struct",
        ]
        assert any(
            re.search(p, content) for p in patterns
        ), "types.go does not define service metrics struct"

    def test_mesh_summary_struct(self):
        """types.go must define a mesh-wide summary struct."""
        content = self._read(self.METRICS_DIR, "types.go")
        patterns = [
            r"type\s+MeshSummary\s+struct",
            r"type\s+MeshMetrics\s+struct",
            r"type\s+\w*Summary\w*\s+struct",
            r"type\s+\w*Mesh\w*\s+struct",
        ]
        assert any(
            re.search(p, content) for p in patterns
        ), "types.go does not define mesh summary struct"

    def test_metrics_include_latency_percentiles(self):
        """Metrics structs must include latency percentiles."""
        content = self._read(self.METRICS_DIR, "types.go")
        patterns = [
            r"P50|p50|P95|p95|P99|p99",
            r"Latency",
            r"latency",
            r"percentile|Percentile",
        ]
        assert any(
            re.search(p, content) for p in patterns
        ), "Metrics do not include latency percentiles"

    def test_metrics_include_request_rate(self):
        """Metrics must include request rate."""
        content = self._read(self.METRICS_DIR, "types.go")
        patterns = [r"RequestRate", r"request_rate", r"RPS", r"RequestCount"]
        assert any(
            re.search(p, content, re.IGNORECASE) for p in patterns
        ), "Metrics do not include request rate"

    def test_metrics_include_success_rate(self):
        """Metrics must include success rate."""
        content = self._read(self.METRICS_DIR, "types.go")
        patterns = [r"SuccessRate", r"success_rate", r"ErrorRate", r"error_rate"]
        assert any(
            re.search(p, content, re.IGNORECASE) for p in patterns
        ), "Metrics do not include success rate"

    # ------------------------------------------------------------------
    # L2: Aggregator logic
    # ------------------------------------------------------------------

    def test_aggregator_has_aggregate_function(self):
        """aggregator.go must have an aggregation function."""
        content = self._read(self.METRICS_DIR, "aggregator.go")
        patterns = [
            r"func\s+.*[Aa]ggregate",
            r"func\s+.*[Cc]ollect",
            r"func\s+.*[Ss]ummarize",
        ]
        assert any(
            re.search(p, content) for p in patterns
        ), "aggregator.go has no aggregation function"

    def test_aggregator_supports_namespace_filter(self):
        """Aggregator must support namespace filtering."""
        content = self._read(self.METRICS_DIR, "aggregator.go")
        patterns = [r"namespace", r"Namespace"]
        assert any(
            re.search(p, content) for p in patterns
        ), "aggregator.go does not support namespace filtering"

    def test_aggregator_handles_time_window(self):
        """Aggregator should support time-windowed aggregation."""
        content = self._read(self.METRICS_DIR, "aggregator.go")
        patterns = [
            r"[Ww]indow",
            r"[Dd]uration",
            r"time\.Duration",
            r"TimeRange",
            r"since",
        ]
        assert any(
            re.search(p, content) for p in patterns
        ), "aggregator.go does not support time windows"

    # ------------------------------------------------------------------
    # L2: HTTP handler
    # ------------------------------------------------------------------

    def test_handler_uses_http(self):
        """handler.go must use net/http to serve metrics."""
        content = self._read(self.METRICS_DIR, "handler.go")
        patterns = [
            r"net/http",
            r"http\.Handler",
            r"http\.ResponseWriter",
            r"ServeHTTP",
            r"HandleFunc",
        ]
        assert any(
            re.search(p, content) for p in patterns
        ), "handler.go does not implement an HTTP handler"

    def test_handler_returns_json(self):
        """Handler must return JSON responses."""
        content = self._read(self.METRICS_DIR, "handler.go")
        patterns = [
            r"encoding/json",
            r"json\.Marshal",
            r"json\.NewEncoder",
            r"application/json",
        ]
        assert any(
            re.search(p, content) for p in patterns
        ), "handler.go does not return JSON"

    def test_handler_supports_query_params(self):
        """Handler must support query parameter filtering."""
        content = self._read(self.METRICS_DIR, "handler.go")
        patterns = [
            r"r\.URL\.Query",
            r"query\.Get",
            r"FormValue",
            r"QueryParam",
            r"ParseForm",
        ]
        assert any(
            re.search(p, content) for p in patterns
        ), "handler.go does not support query parameters"
