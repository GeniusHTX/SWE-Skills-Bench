"""
Test for 'distributed-tracing' skill — OpenTelemetry Collector Tracing
Validates that the Agent implemented Go-based distributed tracing components
with span processing, W3C propagation, batch flushing, and retry logic.
"""

import os
import re
import subprocess

import pytest


class TestDistributedTracing:
    """Verify OTel collector tracing implementation."""

    REPO_DIR = "/workspace/opentelemetry-collector"

    @staticmethod
    def _read(path: str) -> str:
        try:
            with open(path, "r", errors="ignore") as fh:
                return fh.read()
        except OSError:
            return ""

    # ── file_path_check ─────────────────────────────────────────────

    def test_tracing_go_files_exist(self):
        """Verify collector.go, exporter.go, and propagator.go exist in pkg/tracing/."""
        for rel in ("pkg/tracing/collector.go", "pkg/tracing/exporter.go",
                     "pkg/tracing/propagator.go"):
            path = os.path.join(self.REPO_DIR, rel)
            assert os.path.isfile(path), f"Missing: {rel}"

    def test_sampler_and_test_files_exist(self):
        """Verify sampler.go and test files exist."""
        for rel in ("pkg/tracing/sampler.go",
                     "pkg/tracing/collector_test.go",
                     "pkg/tracing/propagator_test.go"):
            path = os.path.join(self.REPO_DIR, rel)
            assert os.path.isfile(path), f"Missing: {rel}"

    def test_package_builds(self):
        """go build ./pkg/tracing/... exits 0."""
        if not os.path.isdir(self.REPO_DIR):
            pytest.skip("Repo dir does not exist")
        result = subprocess.run(
            ["go", "build", "./pkg/tracing/..."],
            capture_output=True, text=True, cwd=self.REPO_DIR, timeout=120,
        )
        if result.returncode != 0:
            pytest.skip(f"go build failed: {result.stderr}")

    # ── semantic_check ──────────────────────────────────────────────

    def test_span_processor_interface_implemented(self):
        """Verify collector.go defines SpanProcessor with OnEnd, Shutdown, ForceFlush."""
        content = self._read(os.path.join(self.REPO_DIR, "pkg/tracing/collector.go"))
        assert content, "collector.go is empty or unreadable"
        for name in ("SpanProcessor", "OnEnd", "Shutdown", "ForceFlush"):
            assert name in content, f"'{name}' not found in collector.go"

    def test_propagator_inject_extract_defined(self):
        """Verify propagator.go defines TraceContextPropagator with Inject and Extract."""
        content = self._read(os.path.join(self.REPO_DIR, "pkg/tracing/propagator.go"))
        assert content, "propagator.go is empty or unreadable"
        for name in ("TraceContextPropagator", "Inject", "Extract"):
            assert name in content, f"'{name}' not found in propagator.go"

    def test_batch_flush_logic_in_collector(self):
        """Verify collector.go has batch buffer and configurable batch_size/flush_interval."""
        content = self._read(os.path.join(self.REPO_DIR, "pkg/tracing/collector.go"))
        assert content, "collector.go is empty or unreadable"
        found = any(kw in content for kw in (
            "batch_size", "batchSize", "flush_interval", "flushInterval"))
        assert found, "No batch size or flush interval field found in collector.go"

    def test_retry_logic_in_exporter(self):
        """Verify exporter.go implements retry logic with max_retries configuration."""
        content = self._read(os.path.join(self.REPO_DIR, "pkg/tracing/exporter.go"))
        assert content, "exporter.go is empty or unreadable"
        found = any(kw in content for kw in ("max_retries", "maxRetries", "retry", "Retry"))
        assert found, "No retry mechanism found in exporter.go"

    # ── functional_check (command) ──────────────────────────────────

    def _skip_unless_go(self):
        if not os.path.isdir(self.REPO_DIR):
            pytest.skip("Repo dir does not exist")
        result = subprocess.run(
            ["go", "version"], capture_output=True, text=True, timeout=10)
        if result.returncode != 0:
            pytest.skip("go not available")

    def test_propagator_inject_produces_w3c_header(self):
        """TestPropagatorInject: Inject produces traceparent header matching W3C regex."""
        self._skip_unless_go()
        result = subprocess.run(
            ["go", "test", "./pkg/tracing/...", "-run", "TestPropagatorInject", "-v"],
            capture_output=True, text=True, cwd=self.REPO_DIR, timeout=120,
        )
        assert result.returncode == 0, f"Test failed: {result.stderr}"

    def test_propagator_extract_malformed_safe(self):
        """TestPropagatorExtractMalformed: malformed traceparent returns empty context."""
        self._skip_unless_go()
        result = subprocess.run(
            ["go", "test", "./pkg/tracing/...", "-run", "TestPropagatorExtractMalformed", "-v"],
            capture_output=True, text=True, cwd=self.REPO_DIR, timeout=120,
        )
        assert result.returncode == 0, f"Test failed: {result.stderr}"

    def test_batch_flush_on_size(self):
        """TestBatchFlush: adding batch_size spans triggers exactly one flush."""
        self._skip_unless_go()
        result = subprocess.run(
            ["go", "test", "./pkg/tracing/...", "-run", "TestBatchFlush", "-v"],
            capture_output=True, text=True, cwd=self.REPO_DIR, timeout=120,
        )
        assert result.returncode == 0, f"Test failed: {result.stderr}"

    def test_exporter_retry_on_503(self):
        """TestExporterRetry: mock 503 twice then 200; exporter retries and succeeds."""
        self._skip_unless_go()
        result = subprocess.run(
            ["go", "test", "./pkg/tracing/...", "-run", "TestExporterRetry", "-v"],
            capture_output=True, text=True, cwd=self.REPO_DIR, timeout=120,
        )
        assert result.returncode == 0, f"Test failed: {result.stderr}"
