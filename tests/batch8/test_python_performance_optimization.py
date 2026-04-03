"""
Test for 'python-performance-optimization' skill — Performance Benchmarks
Validates that the Agent implemented a benchmarking framework with profiler,
analyzer, and reporter modules including statistical percentile computations.
"""

import os
import re
import sys

import pytest


class TestPythonPerformanceOptimization:
    """Verify performance benchmark implementation."""

    REPO_DIR = "/workspace/py-spy"

    @staticmethod
    def _read(path: str) -> str:
        try:
            with open(path, "r", errors="ignore") as fh:
                return fh.read()
        except OSError:
            return ""

    # ── file_path_check ─────────────────────────────────────────────

    def test_benchmark_module_files_exist(self):
        """Verify benchmarks/profiler.py and benchmarks/analyzer.py exist."""
        for rel in ("benchmarks/profiler.py", "benchmarks/analyzer.py"):
            path = os.path.join(self.REPO_DIR, rel)
            assert os.path.isfile(path), f"Missing: {rel}"

    def test_reporter_module_exists(self):
        """Verify benchmarks/reporter.py exists."""
        path = os.path.join(self.REPO_DIR, "benchmarks/reporter.py")
        assert os.path.isfile(path), "Missing: benchmarks/reporter.py"

    # ── semantic_check ──────────────────────────────────────────────

    def test_benchmark_result_fields_defined(self):
        """Verify BenchmarkResult has timings, p95, p99, std_dev fields."""
        content = self._read(os.path.join(self.REPO_DIR, "benchmarks/profiler.py"))
        assert content, "benchmarks/profiler.py is empty or unreadable"
        for kw in ("timings", "p95", "p99", "std_dev"):
            assert kw in content, f"'{kw}' not found in profiler.py"

    def test_regression_error_defined(self):
        """Verify RegressionError and regression threshold 1.20 are defined."""
        content = self._read(os.path.join(self.REPO_DIR, "benchmarks/profiler.py"))
        assert content, "benchmarks/profiler.py is empty or unreadable"
        found = any(kw in content for kw in ("RegressionError", "1.20", "threshold"))
        assert found, "RegressionError or threshold not found in profiler.py"

    def test_performance_report_header_string(self):
        """Verify reporter.py uses '# Performance Report' as the report header."""
        content = self._read(os.path.join(self.REPO_DIR, "benchmarks/reporter.py"))
        assert content, "benchmarks/reporter.py is empty or unreadable"
        assert "# Performance Report" in content, \
            "'# Performance Report' header not found in reporter.py"

    def test_environment_error_for_missing_pyspy(self):
        """Verify analyzer.py raises EnvironmentError when py-spy is not found."""
        content = self._read(os.path.join(self.REPO_DIR, "benchmarks/analyzer.py"))
        assert content, "benchmarks/analyzer.py is empty or unreadable"
        found = any(kw in content for kw in ("EnvironmentError", "py-spy", "shutil.which"))
        assert found, "EnvironmentError or py-spy check not found in analyzer.py"

    # ── functional_check (import) ───────────────────────────────────

    def _skip_unless_importable(self):
        if not os.path.isdir(self.REPO_DIR):
            pytest.skip("Repo dir does not exist")
        if self.REPO_DIR not in sys.path:
            sys.path.insert(0, self.REPO_DIR)

    def test_timing_list_length_equals_iterations(self):
        """BenchmarkRunner.run() returns result with len(timings) == iterations."""
        self._skip_unless_importable()
        try:
            from benchmarks.profiler import BenchmarkRunner
        except Exception as exc:
            pytest.skip(f"Cannot import benchmarks.profiler: {exc}")
        result = BenchmarkRunner().run(lambda: 1 + 1, iterations=50)
        assert len(result.timings) == 50, \
            f"Expected 50 timings, got {len(result.timings)}"

    def test_percentile_ordering_p99_gte_p95_gte_p50(self):
        """BenchmarkResult percentiles satisfy p99 >= p95 >= median >= 0."""
        self._skip_unless_importable()
        try:
            from benchmarks.profiler import BenchmarkRunner
        except Exception as exc:
            pytest.skip(f"Cannot import benchmarks.profiler: {exc}")
        r = BenchmarkRunner().run(lambda: None, iterations=100)
        assert r.p99 >= r.p95 >= r.median >= 0, \
            f"Percentile ordering violated: p99={r.p99} p95={r.p95} median={r.median}"

    def test_mean_calculation(self):
        """BenchmarkResult.mean equals sum(timings)/len(timings) within tolerance."""
        self._skip_unless_importable()
        try:
            from benchmarks.profiler import BenchmarkRunner
        except Exception as exc:
            pytest.skip(f"Cannot import benchmarks.profiler: {exc}")
        r = BenchmarkRunner().run(lambda: None, iterations=20)
        expected = sum(r.timings) / len(r.timings)
        assert abs(r.mean - expected) < 1e-9, \
            f"mean {r.mean} != expected {expected}"

    def test_regression_error_raised_when_p95_exceeds_threshold(self):
        """PerformanceReporter.generate() raises RegressionError when p95 exceeds baseline * 1.20."""
        self._skip_unless_importable()
        try:
            from benchmarks.reporter import PerformanceReporter
            from benchmarks.profiler import BenchmarkResult, RegressionError
        except Exception as exc:
            pytest.skip(f"Cannot import benchmarks modules: {exc}")
        current = BenchmarkResult(
            timings=[150] * 10, mean=150, median=150, p95=150, p99=160, std_dev=0)
        baseline = BenchmarkResult(
            timings=[100] * 10, mean=100, median=100, p95=100, p99=110, std_dev=0)
        with pytest.raises(RegressionError):
            PerformanceReporter().generate(current, baseline)

    def test_report_starts_with_performance_report_header(self):
        """Report string without regression starts with '# Performance Report'."""
        self._skip_unless_importable()
        try:
            from benchmarks.reporter import PerformanceReporter
            from benchmarks.profiler import BenchmarkResult
        except Exception as exc:
            pytest.skip(f"Cannot import benchmarks modules: {exc}")
        r = BenchmarkResult(
            timings=[100] * 10, mean=100, median=100, p95=100, p99=100, std_dev=0)
        report = PerformanceReporter().generate(r, r)
        assert report.startswith("# Performance Report"), \
            "Report must start with '# Performance Report'"
