"""
Test for 'python-performance-optimization' skill — Python Performance Optimization
Validates Benchmark, BenchmarkResult, profile_memory, and find_bottlenecks
for profiling and performance measurement in the py-spy repo.
"""

import os
import sys
import time
import pytest


class TestPythonPerformanceOptimization:
    """Tests for Python performance optimization in the py-spy repo."""

    REPO_DIR = "/workspace/py-spy"

    def _read(self, relpath):
        full = os.path.join(self.REPO_DIR, relpath)
        with open(full, "r", errors="ignore") as f:
            return f.read()

    # --- File Path Checks ---

    def test_benchmark_py_exists(self):
        """Verifies that examples/profiling_toolkit/benchmark.py exists."""
        path = os.path.join(
            self.REPO_DIR, "examples", "profiling_toolkit", "benchmark.py"
        )
        assert os.path.exists(path), f"Expected file not found: {path}"

    def test_init_py_exists(self):
        """Verifies that examples/profiling_toolkit/__init__.py exists."""
        path = os.path.join(
            self.REPO_DIR, "examples", "profiling_toolkit", "__init__.py"
        )
        assert os.path.exists(path), f"Expected file not found: {path}"

    # --- Semantic Checks ---

    def test_sem_import_benchmark(self):
        """Benchmark, BenchmarkResult, profile_memory, find_bottlenecks importable."""
        old_path = sys.path[:]
        try:
            sys.path.insert(0, self.REPO_DIR)
            from examples.profiling_toolkit.benchmark import (
                Benchmark,
                BenchmarkResult,
                profile_memory,
                find_bottlenecks,
            )

            assert Benchmark is not None
            assert BenchmarkResult is not None
        finally:
            sys.path[:] = old_path

    def test_sem_benchmark_has_methods(self):
        """Benchmark has methods: run, profile, compare, warm_up."""
        src = self._read("examples/profiling_toolkit/benchmark.py")
        assert "def run" in src, "Missing run method"
        assert "def profile" in src, "Missing profile method"
        assert "def compare" in src, "Missing compare method"
        assert "def warm_up" in src, "Missing warm_up method"

    def test_sem_benchmark_result_attributes(self):
        """BenchmarkResult has mean_time, median_time, std_time, min_time, etc."""
        src = self._read("examples/profiling_toolkit/benchmark.py")
        assert "mean_time" in src, "Missing mean_time attribute"
        assert "median_time" in src, "Missing median_time attribute"
        assert "std_time" in src, "Missing std_time attribute"
        assert "min_time" in src, "Missing min_time attribute"
        assert "max_time" in src, "Missing max_time attribute"

    def test_sem_benchmark_result_methods(self):
        """BenchmarkResult has methods: to_dict, summary."""
        src = self._read("examples/profiling_toolkit/benchmark.py")
        assert "def to_dict" in src, "Missing to_dict method"
        assert "def summary" in src, "Missing summary method"

    # --- Functional Checks ---

    def test_func_benchmark_run(self):
        """Benchmark.run with sleep(0.001), 20 iterations, mean_time ~ 0.001."""
        old_path = sys.path[:]
        try:
            sys.path.insert(0, self.REPO_DIR)
            from examples.profiling_toolkit.benchmark import Benchmark

            b = Benchmark(lambda: time.sleep(0.001))
            r = b.run(n_iterations=20)
            assert r.mean_time == pytest.approx(0.001, rel=0.5)
        finally:
            sys.path[:] = old_path

    def test_func_time_ordering(self):
        """min_time <= median_time <= max_time."""
        old_path = sys.path[:]
        try:
            sys.path.insert(0, self.REPO_DIR)
            from examples.profiling_toolkit.benchmark import Benchmark

            b = Benchmark(lambda: time.sleep(0.001))
            r = b.run(n_iterations=20)
            assert r.min_time <= r.median_time <= r.max_time
        finally:
            sys.path[:] = old_path

    def test_func_std_non_negative(self):
        """std_time >= 0."""
        old_path = sys.path[:]
        try:
            sys.path.insert(0, self.REPO_DIR)
            from examples.profiling_toolkit.benchmark import Benchmark

            b = Benchmark(lambda: time.sleep(0.001))
            r = b.run(n_iterations=20)
            assert r.std_time >= 0
        finally:
            sys.path[:] = old_path

    def test_func_iterations_count(self):
        """r.iterations == 20."""
        old_path = sys.path[:]
        try:
            sys.path.insert(0, self.REPO_DIR)
            from examples.profiling_toolkit.benchmark import Benchmark

            b = Benchmark(lambda: time.sleep(0.001))
            r = b.run(n_iterations=20)
            assert r.iterations == 20
        finally:
            sys.path[:] = old_path

    def test_func_memory_peak(self):
        """memory_peak_mb >= memory_current_mb."""
        old_path = sys.path[:]
        try:
            sys.path.insert(0, self.REPO_DIR)
            from examples.profiling_toolkit.benchmark import Benchmark

            b = Benchmark(lambda: time.sleep(0.001))
            r = b.run(n_iterations=20)
            assert r.memory_peak_mb >= r.memory_current_mb
        finally:
            sys.path[:] = old_path

    def test_func_zero_iterations_raises(self):
        """Benchmark with n_iterations=0 raises ValueError."""
        old_path = sys.path[:]
        try:
            sys.path.insert(0, self.REPO_DIR)
            from examples.profiling_toolkit.benchmark import Benchmark

            with pytest.raises(ValueError):
                b = Benchmark(lambda: None)
                b.run(n_iterations=0)
        finally:
            sys.path[:] = old_path

    def test_func_compare_speedup(self):
        """Comparing fast vs slow benchmark gives ~10x speedup."""
        old_path = sys.path[:]
        try:
            sys.path.insert(0, self.REPO_DIR)
            from examples.profiling_toolkit.benchmark import Benchmark

            slow = Benchmark(lambda: time.sleep(0.01))
            fast = Benchmark(lambda: time.sleep(0.001))
            cmp = fast.compare(slow)
            assert cmp.speedup == pytest.approx(10.0, rel=0.5)
        finally:
            sys.path[:] = old_path

    def test_func_profile_memory(self):
        """profile_memory returns (result, peak, current) with peak >= current."""
        old_path = sys.path[:]
        try:
            sys.path.insert(0, self.REPO_DIR)
            from examples.profiling_toolkit.benchmark import profile_memory

            result, peak, current = profile_memory(lambda: [0] * 10**6)
            assert peak >= current
        finally:
            sys.path[:] = old_path
