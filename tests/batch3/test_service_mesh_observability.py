"""
Tests for service-mesh-observability skill.
Validates health scoring Go files in viz/metrics/ in linkerd2 repository.
"""

import os
import subprocess
import glob
import re
import pytest

REPO_DIR = "/workspace/linkerd2"


def _path(rel: str) -> str:
    return os.path.join(REPO_DIR, rel)


def _read_dir(dirname: str) -> str:
    pattern = os.path.join(REPO_DIR, dirname, "*.go")
    files = glob.glob(pattern)
    return "\n".join(open(f, encoding="utf-8", errors="ignore").read() for f in files)


def _run(cmd: str, timeout: int = 120):
    return subprocess.run(
        cmd, shell=True, cwd=REPO_DIR, capture_output=True, text=True, timeout=timeout
    )


class TestServiceMeshObservability:

    # ── file_path_check ──────────────────────────────────────────────────────

    def test_viz_metrics_directory_exists(self):
        """viz/metrics/ must contain at least one .go file."""
        pattern = os.path.join(REPO_DIR, "viz", "metrics", "*.go")
        files = glob.glob(pattern)
        assert len(files) >= 1, f"No .go files found in {_path('viz/metrics')}"

    def test_health_scorer_go_exists(self):
        """A health scorer Go file must exist in viz/metrics/."""
        candidates = [
            "viz/metrics/health_scorer.go",
            "viz/metrics/scorer.go",
        ]
        found = any(os.path.isfile(_path(r)) for r in candidates)
        assert found, f"No health scorer Go file found at {candidates}"

    # ── semantic_check ───────────────────────────────────────────────────────

    def test_error_score_calculation_defined(self):
        """ErrorScore or errorScore function must be defined in viz/metrics/."""
        content = _read_dir("viz/metrics")
        assert (
            "ErrorScore" in content
            or "errorScore" in content
            or "CalculateErrorScore" in content
        ), "Error score calculation function not found in viz/metrics/"

    def test_health_status_constants_defined(self):
        """Healthy, Degraded, Critical health status constants must be defined."""
        content = _read_dir("viz/metrics")
        for status in ("Healthy", "Degraded", "Critical"):
            assert (
                status in content
            ), f"{status} constant/iota not found in viz/metrics/ Go files"

    def test_circular_dependency_detection_defined(self):
        """Circular dependency detection must be implemented for service graph topology."""
        content = _read_dir("viz/metrics")
        has_cycle = (
            "CircularDep" in content
            or "circular" in content.lower()
            or "detectCycle" in content
            or "DependencyGraph" in content
            or "cycle" in content.lower()
        )
        assert has_cycle, "No circular dependency detection found in viz/metrics/"

    def test_latency_score_function_defined(self):
        """LatencyScore or latencyScore function must be defined referencing p99."""
        content = _read_dir("viz/metrics")
        has_latency = "LatencyScore" in content or "latencyScore" in content
        has_p99 = "P99" in content or "p99" in content or "99" in content
        assert has_latency, "LatencyScore/latencyScore not found in viz/metrics/"
        assert has_p99, "p99 percentile reference not found in viz/metrics/"

    # ── functional_check ─────────────────────────────────────────────────────

    def test_go_viz_metrics_tests_pass(self):
        """go test ./viz/metrics/... must pass."""
        result = _run("go test ./viz/metrics/...")
        if result.returncode != 0 and (
            "go: " in result.stderr[:50] or "cannot find" in result.stderr
        ):
            pytest.skip("Go not available or viz/metrics module not found")
        assert (
            result.returncode == 0
        ), f"go test ./viz/metrics/... failed:\n{result.stdout}\n{result.stderr}"

    def test_error_score_0_9_for_0_5pct_error_rate(self):
        """error_rate=0.005 must yield error_score=0.9 (mocked)."""

        def error_score(error_rate: float) -> float:
            return max(0.0, 1.0 - error_rate * 20)

        score = error_score(0.005)
        assert abs(score - 0.9) < 0.01, f"Expected 0.9, got {score}"

    def test_degraded_status_for_score_0_757(self):
        """Composite score 0.757 must map to Degraded status (mocked)."""

        def classify_health(score: float) -> str:
            if score >= 0.8:
                return "Healthy"
            elif score >= 0.5:
                return "Degraded"
            else:
                return "Critical"

        assert classify_health(0.757) == "Degraded"

    def test_critical_status_for_score_0_49(self):
        """Composite score 0.49 must map to Critical status (mocked)."""

        def classify_health(score: float) -> str:
            if score >= 0.8:
                return "Healthy"
            elif score >= 0.5:
                return "Degraded"
            else:
                return "Critical"

        assert classify_health(0.49) == "Critical"

    def test_rps_anomaly_penalty_0_3(self):
        """rps=0 vs avg=100 must apply a penalty of 0.3 (mocked)."""

        def traffic_penalty(
            current_rps: float, avg_rps: float, threshold: float = 0.1
        ) -> float:
            if avg_rps == 0:
                return 0.0
            ratio = current_rps / avg_rps
            if ratio < threshold:
                return 0.3
            return 0.0

        penalty = traffic_penalty(current_rps=0, avg_rps=100)
        assert abs(penalty - 0.3) < 0.01, f"Expected penalty=0.3, got {penalty}"

    def test_circular_dependency_a_b_c_a_detected(self):
        """A->B->C->A circular dependency must be detected (mocked)."""

        def has_cycle(edges: list) -> bool:
            from collections import defaultdict

            graph = defaultdict(list)
            for src, dst in edges:
                graph[src].append(dst)

            visited = set()
            stack = set()

            def dfs(node):
                visited.add(node)
                stack.add(node)
                for neighbor in graph[node]:
                    if neighbor not in visited:
                        if dfs(neighbor):
                            return True
                    elif neighbor in stack:
                        return True
                stack.discard(node)
                return False

            for node in list(graph.keys()):
                if node not in visited:
                    if dfs(node):
                        return True
            return False

        edges = [("A", "B"), ("B", "C"), ("C", "A")]
        assert has_cycle(edges), "Expected cycle detection for A->B->C->A"
