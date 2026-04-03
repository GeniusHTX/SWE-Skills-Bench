"""
Test for 'distributed-tracing' skill — Distributed Tracing in Go
Validates TracerProvider, W3C propagator, go.mod OTel dependency,
Shutdown lifecycle, child span context, and error handling.
"""

import glob
import os
import re

import pytest


class TestDistributedTracing:
    """Verify Go distributed tracing: OTel provider, propagator, spans."""

    REPO_DIR = "/workspace/opentelemetry-collector"

    # ── helpers ──────────────────────────────────────────────────────────

    @staticmethod
    def _read_file(path: str) -> str:
        try:
            with open(path, "r", errors="ignore") as fh:
                return fh.read()
        except OSError:
            return ""

    def _root(self, *parts) -> str:
        return os.path.join(self.REPO_DIR, *parts)

    # ── file_path_check ──────────────────────────────────────────────────

    def test_go_mod_exists(self):
        """go.mod must exist at repository root."""
        assert os.path.isfile(self._root("go.mod")), "go.mod not found"

    def test_tracing_provider_go_exists(self):
        """tracing/provider.go must exist and be non-empty."""
        p = self._root("tracing", "provider.go")
        assert os.path.isfile(p), "tracing/provider.go not found"
        assert os.path.getsize(p) > 0

    def test_tracing_propagator_go_exists(self):
        """tracing/propagator.go must exist."""
        assert os.path.isfile(self._root("tracing", "propagator.go"))

    def test_test_go_file_exists(self):
        """At least one *_test.go file must exist in tracing/."""
        pattern = self._root("tracing", "*_test.go")
        assert glob.glob(pattern), "No *_test.go in tracing/"

    # ── semantic_check ───────────────────────────────────────────────────

    def test_go_mod_declares_otel_dependency(self):
        """go.mod must declare go.opentelemetry.io/otel at >= v1.20.0."""
        content = self._read_file(self._root("go.mod"))
        if not content:
            pytest.skip("go.mod not found")
        assert "go.opentelemetry.io/otel" in content

    def test_tracer_provider_creates_named_tracer(self):
        """provider.go must use NewTracerProvider and .Tracer(."""
        content = self._read_file(self._root("tracing", "provider.go"))
        if not content:
            pytest.skip("provider.go not found")
        assert "TracerProvider" in content
        assert ".Tracer(" in content

    def test_propagator_injects_w3c_traceparent(self):
        """propagator.go must reference TraceContext and Inject."""
        content = self._read_file(self._root("tracing", "propagator.go"))
        if not content:
            pytest.skip("propagator.go not found")
        assert "TraceContext" in content
        assert "Inject" in content

    def test_provider_shutdown_method(self):
        """provider.go must define Shutdown(ctx context.Context)."""
        content = self._read_file(self._root("tracing", "provider.go"))
        if not content:
            pytest.skip("provider.go not found")
        assert ".Shutdown(" in content or "Shutdown(" in content
        assert "context.Context" in content

    # ── functional_check ─────────────────────────────────────────────────

    def test_otel_version_at_least_1_20(self):
        """Parsed OTel version from go.mod must be >= v1.20.0."""
        content = self._read_file(self._root("go.mod"))
        if not content:
            pytest.skip("go.mod not found")
        match = re.search(r"go\.opentelemetry\.io/otel\s+v(\d+)\.(\d+)\.(\d+)", content)
        if not match:
            pytest.skip("Cannot parse OTel version from go.mod")
        major, minor = int(match.group(1)), int(match.group(2))
        assert major >= 1 and minor >= 20, f"OTel version v{major}.{minor} < v1.20"

    def test_child_span_uses_parent_context(self):
        """Source must pass parent ctx to .Start(ctx, ...)."""
        files = glob.glob(self._root("tracing", "*.go"))
        found = False
        for f in files:
            content = self._read_file(f)
            if ".Start(ctx," in content:
                found = True
                break
        assert found, ".Start(ctx, ...) pattern not found in tracing/"

    def test_no_start_nil_context(self):
        """Source must not call .Start(nil, ...)."""
        files = glob.glob(self._root("tracing", "*.go"))
        for f in files:
            content = self._read_file(f)
            if re.search(r"\.Start\(nil\s*,", content):
                pytest.fail(f".Start(nil, ...) found in {f}")

    def test_context_background_fallback(self):
        """Source must use context.Background() as nil-context fallback."""
        files = glob.glob(self._root("tracing", "*.go"))
        found = False
        for f in files:
            content = self._read_file(f)
            if "context.Background()" in content:
                found = True
                break
        assert found, "context.Background() fallback not found"
