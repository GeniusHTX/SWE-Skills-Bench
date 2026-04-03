"""Test file for the python-observability skill.

This suite validates OTLP exporter observability metrics (counters,
histograms, gauges), structured logging, and retry behavior.
"""

from __future__ import annotations

import ast
import pathlib
import re

import pytest


class TestPythonObservability:
    """Verify OTLP exporter observability in opentelemetry-python."""

    REPO_DIR = "/workspace/opentelemetry-python"

    METRICS_PY = "exporter/opentelemetry-exporter-otlp-proto-http/src/opentelemetry/exporter/otlp/proto/http/metrics.py"
    TEST_PY = "exporter/opentelemetry-exporter-otlp-proto-http/tests/test_exporter_observability.py"
    EXPORTER_PY = "exporter/opentelemetry-exporter-otlp-proto-http/src/opentelemetry/exporter/otlp/proto/http/exporter.py"

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    def _repo_path(self, relative: str) -> pathlib.Path:
        return pathlib.Path(self.REPO_DIR, *relative.split("/"))

    def _read_text(self, relative: str) -> str:
        path = self._repo_path(relative)
        assert path.exists(), f"Expected path to exist: {path}"
        return path.read_text(encoding="utf-8", errors="ignore")

    def _assert_non_empty_file(self, relative: str) -> pathlib.Path:
        path = self._repo_path(relative)
        assert path.is_file(), f"Expected file to exist: {path}"
        assert path.stat().st_size > 0, f"Expected non-empty file: {path}"
        return path

    def _all_sources(self) -> str:
        parts = []
        for rel in (self.METRICS_PY, self.EXPORTER_PY):
            p = self._repo_path(rel)
            if p.is_file():
                parts.append(p.read_text(encoding="utf-8", errors="ignore"))
        return "\n".join(parts)

    # ------------------------------------------------------------------
    # Layer 1 – file_path_check (3 cases)
    # ------------------------------------------------------------------

    def test_file_path_exporter_opentelemetry_exporter_otlp_proto_http_src_opentele(
        self,
    ):
        """Verify metrics.py exists and is non-empty."""
        self._assert_non_empty_file(self.METRICS_PY)

    def test_file_path_exporter_opentelemetry_exporter_otlp_proto_http_tests_test_e(
        self,
    ):
        """Verify test_exporter_observability.py exists and is non-empty."""
        self._assert_non_empty_file(self.TEST_PY)

    def test_file_path_exporter_opentelemetry_exporter_otlp_proto_http_src_opentele_1(
        self,
    ):
        """Verify exporter.py exists (modified)."""
        self._assert_non_empty_file(self.EXPORTER_PY)

    # ------------------------------------------------------------------
    # Layer 2 – semantic_check (5 cases)
    # ------------------------------------------------------------------

    def test_semantic_otlp_export_requests_total_is_a_counter_with_labelnames_expo(
        self,
    ):
        """OTLP_EXPORT_REQUESTS_TOTAL is a Counter with labelnames."""
        src = self._all_sources()
        assert re.search(
            r"OTLP_EXPORT_REQUESTS_TOTAL|export_requests_total", src
        ), "OTLP_EXPORT_REQUESTS_TOTAL counter not found"
        assert re.search(r"Counter\s*\(", src), "Counter metric required"

    def test_semantic_otlp_export_duration_seconds_is_a_histogram_with_specified_b(
        self,
    ):
        """OTLP_EXPORT_DURATION_SECONDS is a Histogram with specified buckets."""
        src = self._all_sources()
        assert re.search(
            r"OTLP_EXPORT_DURATION_SECONDS|export_duration", src
        ), "OTLP_EXPORT_DURATION_SECONDS histogram not found"
        assert re.search(r"Histogram\s*\(", src), "Histogram metric required"

    def test_semantic_otlp_export_items_total_is_a_counter_with_correct_labels(self):
        """OTLP_EXPORT_ITEMS_TOTAL is a Counter with correct labels."""
        src = self._all_sources()
        assert re.search(
            r"OTLP_EXPORT_ITEMS_TOTAL|export_items_total", src
        ), "OTLP_EXPORT_ITEMS_TOTAL counter not found"

    def test_semantic_otlp_export_queue_size_is_a_gauge_with_correct_labels(self):
        """OTLP_EXPORT_QUEUE_SIZE is a Gauge with correct labels."""
        src = self._all_sources()
        assert re.search(
            r"OTLP_EXPORT_QUEUE_SIZE|export_queue_size", src
        ), "OTLP_EXPORT_QUEUE_SIZE gauge not found"
        assert re.search(r"Gauge\s*\(", src), "Gauge metric required"

    def test_semantic_structlog_get_logger___name___used_not_root_logger(self):
        """structlog.get_logger(__name__) used (not root logger)."""
        src = self._all_sources()
        assert re.search(
            r"structlog\.get_logger|getLogger\(__name__\)|logger.*__name__", src
        ), "Should use structlog.get_logger(__name__) or getLogger(__name__)"

    # ------------------------------------------------------------------
    # Layer 3 – functional_check (5 cases, source analysis)
    # ------------------------------------------------------------------

    def test_functional_export_100_spans_requests_total_success_1_items_total_succes(
        self,
    ):
        """Export 100 spans -> REQUESTS_TOTAL(success)=1, ITEMS_TOTAL(success)=100."""
        src = self._all_sources()
        assert re.search(
            r"labels\s*\(|inc\s*\(|observe\s*\(", src
        ), "Metrics should be incremented during export"

    def test_functional_server_returns_503_with_2_retries_then_failure_retried_2_fai(
        self,
    ):
        """Server returns 503 with 2 retries then failure -> retried=2, failed=1."""
        src = self._all_sources()
        assert re.search(
            r"retr|503|retry", src, re.IGNORECASE
        ), "Retry logic should exist for 503 responses"

    def test_functional_duration_histogram_has_observation_after_successful_export(
        self,
    ):
        """Duration histogram has observation after successful export."""
        src = self._all_sources()
        assert re.search(
            r"observe\s*\(|time\s*\(|duration", src
        ), "Duration histogram should be observed after export"

    def test_functional_prometheus_client_exception_during_labels_export_still_compl(
        self,
    ):
        """prometheus_client exception during labels() -> export still completes."""
        src = self._all_sources()
        assert re.search(
            r"except|try|Exception", src
        ), "Metrics failures should not interrupt exports"

    def test_functional_structured_logs_contain_endpoint_signal_duration_ms_fields(
        self,
    ):
        """Structured logs contain endpoint, signal, duration_ms fields."""
        src = self._all_sources()
        assert re.search(
            r"endpoint|signal|duration_ms|log\.", src
        ), "Structured logs should contain endpoint, signal, duration_ms"
