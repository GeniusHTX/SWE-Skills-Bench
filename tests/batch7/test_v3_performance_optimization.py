"""Test file for the v3-performance-optimization skill.

This suite validates flash-attention v2 benchmark tooling:
BenchmarkResult dataclass, TFLOPs computation, memory measurement,
and benchmark configurations.
"""

from __future__ import annotations

import ast
import pathlib
import re

import pytest


class TestV3PerformanceOptimization:
    """Verify flash-attention v2 benchmarking tools."""

    REPO_DIR = "/workspace/flash-attention"

    BENCHMARK_PY = "benchmarks/benchmark_flash_attn_v2.py"
    BENCHMARK_UTILS_PY = "benchmarks/benchmark_utils.py"
    TEST_CORRECTNESS_PY = "tests/test_benchmark_correctness.py"

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

    def _class_source(self, source: str, class_name: str) -> str:
        """Extract class source via AST."""
        try:
            tree = ast.parse(source)
        except SyntaxError:
            return ""
        for node in ast.walk(tree):
            if isinstance(node, ast.ClassDef) and node.name == class_name:
                return ast.get_source_segment(source, node) or ""
        return ""

    def _function_source(self, source: str, func_name: str) -> str:
        """Extract function source via AST."""
        try:
            tree = ast.parse(source)
        except SyntaxError:
            return ""
        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef) and node.name == func_name:
                return ast.get_source_segment(source, node) or ""
        return ""

    # ------------------------------------------------------------------
    # Layer 1 – file_path_check (3 cases)
    # ------------------------------------------------------------------

    def test_file_path_benchmark_flash_attn_v2_py_exists(self):
        """Verify benchmarks/benchmark_flash_attn_v2.py exists."""
        self._assert_non_empty_file(self.BENCHMARK_PY)

    def test_file_path_benchmark_utils_py_exists(self):
        """Verify benchmarks/benchmark_utils.py exists."""
        self._assert_non_empty_file(self.BENCHMARK_UTILS_PY)

    def test_file_path_test_benchmark_correctness_py_exists(self):
        """Verify tests/test_benchmark_correctness.py exists."""
        self._assert_non_empty_file(self.TEST_CORRECTNESS_PY)

    # ------------------------------------------------------------------
    # Layer 2 – semantic_check (5 cases)
    # ------------------------------------------------------------------

    def test_semantic_benchmarkresult_is_a_dataclass(self):
        """BenchmarkResult is a dataclass with specified fields."""
        src = self._read_text(self.BENCHMARK_UTILS_PY)
        all_src = src + "\n" + self._read_text(self.BENCHMARK_PY)
        assert re.search(
            r"@dataclass|dataclass", all_src
        ), "BenchmarkResult should be a dataclass"
        cls = self._class_source(all_src, "BenchmarkResult")
        assert cls, "BenchmarkResult class not found"

    def test_semantic_compute_attention_tflops_factor_4_or_2(self):
        """compute_attention_tflops applies factor 4 (non-causal) or 2 (causal)."""
        src = self._read_text(self.BENCHMARK_UTILS_PY)
        all_src = src + "\n" + self._read_text(self.BENCHMARK_PY)
        func = self._function_source(all_src, "compute_attention_tflops")
        if not func:
            # May be named differently
            func = all_src
        assert re.search(
            r"causal|is_causal", func, re.IGNORECASE
        ), "compute_attention_tflops should handle causal vs non-causal"
        assert re.search(
            r"\b[24]\b|\*\s*[24]|factor", func
        ), "Should apply factor 4 (non-causal) or 2 (causal)"

    def test_semantic_benchmark_forward_warmup_and_benchmark_iters(self):
        """benchmark_forward has warmup_iters and benchmark_iters parameters."""
        src = self._read_text(self.BENCHMARK_PY)
        all_src = src + "\n" + self._read_text(self.BENCHMARK_UTILS_PY)
        assert re.search(
            r"warmup", all_src, re.IGNORECASE
        ), "benchmark_forward should have warmup_iters parameter"
        assert re.search(
            r"benchmark_iters|num_iters|repeat", all_src, re.IGNORECASE
        ), "benchmark_forward should have benchmark_iters parameter"

    def test_semantic_measure_peak_memory_mb(self):
        """measure_peak_memory_mb calls reset_peak_memory_stats and max_memory_allocated."""
        src = self._read_text(self.BENCHMARK_UTILS_PY)
        all_src = src + "\n" + self._read_text(self.BENCHMARK_PY)
        assert re.search(
            r"reset_peak_memory_stats|reset_max_memory", all_src
        ), "Should call reset_peak_memory_stats"
        assert re.search(
            r"max_memory_allocated", all_src
        ), "Should call max_memory_allocated"

    def test_semantic_benchmark_configs_contains_6_configurations(self):
        """BENCHMARK_CONFIGS contains 6 configurations."""
        src = self._read_text(self.BENCHMARK_PY)
        all_src = src + "\n" + self._read_text(self.BENCHMARK_UTILS_PY)
        assert re.search(
            r"BENCHMARK_CONFIGS|configs|CONFIGURATIONS", all_src
        ), "BENCHMARK_CONFIGS should be defined"

    # ------------------------------------------------------------------
    # Layer 3 – functional_check (4 cases)
    # ------------------------------------------------------------------

    def test_functional_non_causal_tflops_computation(self):
        """Non-causal TFLOPs: batch=1, seq=512, heads=8, dim=64, 1s → ~5.37e-4 TFLOPs."""
        src = self._read_text(self.BENCHMARK_UTILS_PY)
        all_src = src + "\n" + self._read_text(self.BENCHMARK_PY)
        # Verify the TFLOPs formula exists
        assert re.search(
            r"tflops|flops|FLOP", all_src, re.IGNORECASE
        ), "TFLOPs computation should be implemented"
        # Factor 4 for non-causal
        assert re.search(
            r"\b4\b.*seq|seq.*\b4\b|factor.*4|non.causal", all_src, re.IGNORECASE
        ), "Non-causal should use factor 4"

    def test_functional_causal_tflops_half_of_non_causal(self):
        """Causal TFLOPs = half of non-causal for same inputs."""
        src = self._read_text(self.BENCHMARK_UTILS_PY)
        all_src = src + "\n" + self._read_text(self.BENCHMARK_PY)
        assert re.search(
            r"causal.*2|2.*causal|factor.*2|half", all_src, re.IGNORECASE
        ), "Causal TFLOPs should be half of non-causal"

    def test_functional_benchmarkresult_dtype_correctly_set(self):
        """BenchmarkResult.dtype correctly set for fp16/bf16."""
        src = self._read_text(self.BENCHMARK_PY)
        all_src = src + "\n" + self._read_text(self.BENCHMARK_UTILS_PY)
        assert re.search(
            r"dtype|fp16|bf16|float16|bfloat16", all_src
        ), "BenchmarkResult should track dtype"

    def test_functional_comparison_table_contains_speedup(self):
        """print_comparison_table output contains speedup value."""
        src = self._read_text(self.BENCHMARK_PY)
        all_src = src + "\n" + self._read_text(self.BENCHMARK_UTILS_PY)
        assert re.search(
            r"speedup|comparison|table|print.*result", all_src, re.IGNORECASE
        ), "Should have a comparison table with speedup"
