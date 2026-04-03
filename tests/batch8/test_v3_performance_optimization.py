"""
Test for 'v3-performance-optimization' skill — Flash Attention Performance
Validates that the Agent implemented attention benchmark, kernel profiler,
and performance summary modules with CUDA availability gates and TFLOPS metrics.
"""

import os
import re
import sys

import pytest


class TestV3PerformanceOptimization:
    """Verify Flash Attention performance optimization implementation."""

    REPO_DIR = "/workspace/flash-attention"

    @staticmethod
    def _read(path: str) -> str:
        try:
            with open(path, "r", errors="ignore") as fh:
                return fh.read()
        except OSError:
            return ""

    def _find_file(self, *candidates):
        for c in candidates:
            p = os.path.join(self.REPO_DIR, c)
            if os.path.isfile(p):
                return p
        return None

    # ── file_path_check ─────────────────────────────────────────────

    def test_attention_benchmark_module_exists(self):
        """Verify v3_performance/attention_benchmark.py or benchmark.py exists."""
        candidates = ("v3_performance/attention_benchmark.py", "benchmark.py")
        found = any(
            os.path.isfile(os.path.join(self.REPO_DIR, c)) for c in candidates)
        assert found, f"Missing: none of {candidates} found"

    def test_kernel_profiler_module_exists(self):
        """Verify v3_performance/kernel_profiler.py or profiler.py exists."""
        candidates = ("v3_performance/kernel_profiler.py", "profiler.py")
        found = any(
            os.path.isfile(os.path.join(self.REPO_DIR, c)) for c in candidates)
        assert found, f"Missing: none of {candidates} found"

    def test_performance_summary_module_exists(self):
        """Verify v3_performance/performance_summary.py or summary.py exists."""
        candidates = ("v3_performance/performance_summary.py", "summary.py")
        found = any(
            os.path.isfile(os.path.join(self.REPO_DIR, c)) for c in candidates)
        assert found, f"Missing: none of {candidates} found"

    # ── semantic_check ──────────────────────────────────────────────

    def test_cuda_availability_gate(self):
        """Verify torch.cuda.is_available() is checked before CUDA operations."""
        path = self._find_file("v3_performance/attention_benchmark.py",
                               "benchmark.py")
        assert path, "Benchmark module not found"
        content = self._read(path)
        assert "cuda.is_available" in content, \
            "cuda.is_available guard not found"

    def test_profiler_timing_reference(self):
        """Verify triton.testing.do_bench or torch.profiler is used for timing."""
        path = self._find_file("v3_performance/kernel_profiler.py", "profiler.py")
        assert path, "Profiler module not found"
        content = self._read(path)
        found = any(kw in content for kw in (
            "do_bench", "torch.profiler", "time.perf_counter"))
        assert found, "No timing mechanism found in profiler"

    def test_speedup_calculation_present(self):
        """Verify speedup or ratio calculation is present in PerformanceSummary."""
        path = self._find_file("v3_performance/performance_summary.py",
                               "summary.py")
        assert path, "Performance summary module not found"
        content = self._read(path)
        found = any(kw in content for kw in (
            "speedup", "baseline_time", "optimized_time"))
        assert found, "Speedup calculation not found"

    def test_tflops_metric_present(self):
        """Verify TFLOPS or throughput metric is computed."""
        path = self._find_file("v3_performance/performance_summary.py",
                               "summary.py")
        assert path, "Performance summary module not found"
        content = self._read(path)
        found = any(kw in content.lower() for kw in ("tflops", "throughput"))
        assert found, "TFLOPS or throughput metric not found"

    # ── functional_check (import) ───────────────────────────────────

    def _skip_unless_importable(self):
        if not os.path.isdir(self.REPO_DIR):
            pytest.skip("Repo dir does not exist")
        if self.REPO_DIR not in sys.path:
            sys.path.insert(0, self.REPO_DIR)

    def test_kernel_profiler_returns_positive_time(self):
        """KernelProfiler.profile(lambda: sum(range(1000))) returns positive value."""
        self._skip_unless_importable()
        try:
            from v3_performance.kernel_profiler import KernelProfiler
        except Exception as exc:
            pytest.skip(f"Cannot import: {exc}")
        t = KernelProfiler().profile(lambda: sum(range(1000)))
        assert isinstance(t, (int, float)) and t > 0, \
            f"Expected positive time, got {t}"

    def test_performance_summary_speedup_with_mock(self):
        """PerformanceSummary.report() with mock data yields speedup > 1.0."""
        self._skip_unless_importable()
        try:
            from v3_performance.performance_summary import PerformanceSummary
        except Exception as exc:
            pytest.skip(f"Cannot import: {exc}")
        rows = PerformanceSummary().report(
            standard_ms=10.0, flash_ms=3.0, seq_len=512)
        assert isinstance(rows, list) and len(rows) > 0, \
            "report() must return non-empty list"
        assert rows[0]["speedup"] > 1.0, \
            f"Expected speedup > 1.0, got {rows[0]['speedup']}"

    def test_cuda_unavailable_run_returns_none_or_empty(self):
        """AttentionBenchmark.run([512]) returns None/empty on CPU-only host."""
        self._skip_unless_importable()
        try:
            from unittest.mock import patch
            from v3_performance.attention_benchmark import AttentionBenchmark
        except Exception as exc:
            pytest.skip(f"Cannot import: {exc}")
        with patch("torch.cuda.is_available", return_value=False):
            result = AttentionBenchmark().run([512])
        assert result is None or result == {} or result == [], \
            f"Expected None/empty on CPU-only, got {result}"
