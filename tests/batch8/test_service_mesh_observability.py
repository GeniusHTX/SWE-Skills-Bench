"""
Test for 'service-mesh-observability' skill — Service Mesh Health Summary
Validates that the Agent implemented Go-based service mesh observability
with latency percentiles, success rate thresholds, and control plane diagnostics.
"""

import os
import re
import subprocess

import pytest


class TestServiceMeshObservability:
    """Verify service mesh observability implementation."""

    REPO_DIR = "/workspace/linkerd2"

    @staticmethod
    def _read(path: str) -> str:
        try:
            with open(path, "r", errors="ignore") as fh:
                return fh.read()
        except OSError:
            return ""

    # ── file_path_check ─────────────────────────────────────────────

    def test_collector_module_exists(self):
        """Verify healthsummary/collector.go exists."""
        path = os.path.join(self.REPO_DIR, "healthsummary/collector.go")
        assert os.path.isfile(path), "Missing: healthsummary/collector.go"

    def test_aggregator_and_diagnostics_exist(self):
        """Verify healthsummary/aggregator.go and diagnostics.go exist."""
        for rel in ("healthsummary/aggregator.go",
                     "healthsummary/diagnostics.go"):
            path = os.path.join(self.REPO_DIR, rel)
            assert os.path.isfile(path), f"Missing: {rel}"

    def test_go_mod_exists(self):
        """Verify go.mod exists at project root."""
        path = os.path.join(self.REPO_DIR, "go.mod")
        assert os.path.isfile(path), "Missing: go.mod"

    # ── semantic_check ──────────────────────────────────────────────

    def test_latency_percentile_fields_defined(self):
        """Verify health summary struct has P50, P95, P99 latency fields."""
        content = self._read(os.path.join(
            self.REPO_DIR, "healthsummary/aggregator.go"))
        assert content, "aggregator.go is empty or unreadable"
        for field in ("P50", "P95", "P99"):
            assert field in content, f"'{field}' not found in aggregator.go"

    def test_success_rate_threshold_defined(self):
        """Verify 0.99 success rate threshold is referenced for degraded flagging."""
        content = self._read(os.path.join(
            self.REPO_DIR, "healthsummary/aggregator.go"))
        assert content, "aggregator.go is empty or unreadable"
        assert "0.99" in content, "0.99 threshold not found in aggregator.go"

    def test_control_plane_status_constants(self):
        """Verify diagnostics.go defines OK, DEGRADED, and DOWN status constants."""
        content = self._read(os.path.join(
            self.REPO_DIR, "healthsummary/diagnostics.go"))
        assert content, "diagnostics.go is empty or unreadable"
        for status in ("OK", "DEGRADED", "DOWN"):
            assert status in content, f"'{status}' not found in diagnostics.go"

    # ── functional_check (command) ──────────────────────────────────

    def _skip_unless_go(self):
        if not os.path.isdir(self.REPO_DIR):
            pytest.skip("Repo dir does not exist")
        result = subprocess.run(
            ["go", "version"], capture_output=True, text=True, timeout=10)
        if result.returncode != 0:
            pytest.skip("go not available")

    def test_go_test_passes(self):
        """go test ./... exits 0, all unit tests pass."""
        self._skip_unless_go()
        result = subprocess.run(
            ["go", "test", "./..."],
            capture_output=True, text=True, cwd=self.REPO_DIR, timeout=120,
        )
        assert result.returncode == 0, f"go test failed: {result.stderr}"

    def test_go_vet_passes(self):
        """go vet ./... exits 0 with no static analysis issues."""
        self._skip_unless_go()
        result = subprocess.run(
            ["go", "vet", "./..."],
            capture_output=True, text=True, cwd=self.REPO_DIR, timeout=120,
        )
        assert result.returncode == 0, f"go vet failed: {result.stderr}"

    def test_low_success_rate_service_flagged_as_degraded(self):
        """Service with 95% success rate is included in the degraded services list."""
        self._skip_unless_go()
        result = subprocess.run(
            ["go", "test", "./...", "-run", "TestDegradedServiceFlagging", "-v"],
            capture_output=True, text=True, cwd=self.REPO_DIR, timeout=120,
        )
        assert result.returncode == 0, f"Test failed: {result.stderr}"
        assert "DEGRADED" in result.stdout or "DEGRADED" in result.stderr, \
            "DEGRADED not found in test output"

    def test_empty_namespace_returns_empty_summary(self):
        """Collect() on empty namespace returns empty summary without error."""
        self._skip_unless_go()
        result = subprocess.run(
            ["go", "test", "./...", "-run", "TestEmptyNamespace", "-v"],
            capture_output=True, text=True, cwd=self.REPO_DIR, timeout=120,
        )
        assert result.returncode == 0, f"Test failed: {result.stderr}"
