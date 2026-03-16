"""
Test for 'service-mesh-observability' skill — Linkerd TCP Metrics Collection
Validates that the Agent added TCP connection metrics collection code with
Prometheus metric exposition in the Linkerd2 viz package.
"""

import os
import subprocess
import pytest

from _dependency_utils import ensure_go_dependencies


@pytest.fixture(scope="module", autouse=True)
def _ensure_repo_dependencies():
    ensure_go_dependencies(TestServiceMeshObservability.REPO_DIR)


class TestServiceMeshObservability:
    """Verify TCP metrics collection demo in Linkerd2."""

    REPO_DIR = "/workspace/linkerd2"

    # ------------------------------------------------------------------
    # L1: file existence
    # ------------------------------------------------------------------

    def test_tcp_metrics_demo_exists(self):
        """viz/metrics-api/examples/tcp_metrics_demo.go must exist."""
        fpath = os.path.join(
            self.REPO_DIR, "viz", "metrics-api", "examples", "tcp_metrics_demo.go"
        )
        assert os.path.isfile(fpath), "tcp_metrics_demo.go not found"

    def test_readme_exists(self):
        """viz/metrics-api/examples/README.md must exist."""
        fpath = os.path.join(
            self.REPO_DIR, "viz", "metrics-api", "examples", "README.md"
        )
        assert os.path.isfile(fpath), "README.md not found"

    # ------------------------------------------------------------------
    # L2: content verification
    # ------------------------------------------------------------------

    def _read_demo(self):
        fpath = os.path.join(
            self.REPO_DIR, "viz", "metrics-api", "examples", "tcp_metrics_demo.go"
        )
        with open(fpath, "r", encoding="utf-8") as f:
            return f.read()

    def test_tcp_open_total_metric(self):
        """Must define tcp_open_total metric."""
        source = self._read_demo()
        assert "tcp_open_total" in source, "tcp_open_total metric not defined"

    def test_tcp_close_total_metric(self):
        """Must define tcp_close_total metric."""
        source = self._read_demo()
        assert "tcp_close_total" in source, "tcp_close_total metric not defined"

    def test_tcp_connection_duration_metric(self):
        """Must define tcp_connection_duration metric."""
        source = self._read_demo()
        assert (
            "tcp_connection_duration" in source
        ), "tcp_connection_duration metric not defined"

    def test_tcp_read_bytes_metric(self):
        """Must define tcp_read_bytes_total metric."""
        source = self._read_demo()
        assert "tcp_read_bytes" in source, "tcp_read_bytes metric not defined"

    def test_tcp_write_bytes_metric(self):
        """Must define tcp_write_bytes_total metric."""
        source = self._read_demo()
        assert "tcp_write_bytes" in source, "tcp_write_bytes metric not defined"

    def test_prometheus_import(self):
        """Must import Prometheus client library."""
        source = self._read_demo()
        prom_patterns = ["prometheus", "promauto", "promhttp"]
        assert any(
            p in source for p in prom_patterns
        ), "No Prometheus library import found"

    def test_histogram_bucketing(self):
        """Duration metric should use histogram bucketing."""
        source = self._read_demo()
        histogram_patterns = [
            "Histogram",
            "NewHistogram",
            "HistogramVec",
            "Buckets",
            "histogram",
        ]
        found = any(p in source for p in histogram_patterns)
        assert found, "No histogram definition found for duration metric"

    def test_go_build_viz(self):
        """go build ./viz/... must succeed."""
        result = subprocess.run(
            ["go", "build", "./viz/..."],
            cwd=self.REPO_DIR,
            capture_output=True,
            text=True,
            timeout=600,
        )
        assert result.returncode == 0, f"Build failed:\n{result.stderr}"

    def test_readme_documents_metrics(self):
        """README must document the TCP metrics."""
        fpath = os.path.join(
            self.REPO_DIR, "viz", "metrics-api", "examples", "README.md"
        )
        with open(fpath, "r", encoding="utf-8") as f:
            content = f.read()
        assert "tcp" in content.lower(), "README doesn't mention TCP metrics"
        assert len(content) >= 100, "README is too short"

    def test_go_vet_passes(self):
        """go vet should pass on the demo file."""
        result = subprocess.run(
            ["go", "vet", "./viz/metrics-api/examples/..."],
            cwd=self.REPO_DIR,
            capture_output=True,
            text=True,
            timeout=120,
        )
        # go vet may warn but should not error
        assert result.returncode == 0, f"go vet failed:\n{result.stderr}"
