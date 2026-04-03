"""
Test for 'v3-performance-optimization' skill — Flash Attention Benchmarks
Validates benchmark files, BenchmarkResult dataclass, compute_tflops,
causal 0.5 multiplier, CUDA skip guards, and shape assertions.
"""

import os
import sys

import pytest


class TestV3PerformanceOptimization:
    """Verify flash attention benchmark suite: tflops, shapes, OOM guard."""

    REPO_DIR = "/workspace/flash-attention"

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

    def test_benchmark_files_exist(self):
        """Four benchmark .py files must exist."""
        for name in (
            "benchmark_flash_attention.py",
            "benchmark_backward.py",
            "memory_efficiency.py",
            "utils.py",
        ):
            path = self._root("benchmarks", name)
            assert os.path.isfile(path), f"{name} not found"

    def test_test_files_exist(self):
        """Three test files must exist in tests/."""
        for name in (
            "test_flash_attn_correctness.py",
            "test_flash_attn_shapes.py",
            "test_varlen_attention.py",
        ):
            path = self._root("tests", name)
            assert os.path.isfile(path), f"{name} not found"

    def test_benchmark_result_dataclass(self):
        """BenchmarkResult must have mean_ms and tflops fields."""
        content = self._read_file(self._root("benchmarks", "utils.py"))
        if not content:
            pytest.skip("utils.py not found")
        assert "BenchmarkResult" in content
        assert "mean_ms" in content
        assert "tflops" in content

    # ── semantic_check ───────────────────────────────────────────────────

    def test_benchmark_forward_warmup_repeats(self):
        """benchmark_forward must have repeats and warmup parameters."""
        content = self._read_file(self._root("benchmarks", "utils.py"))
        if not content:
            pytest.skip("utils.py not found")
        assert "def benchmark_forward" in content
        assert "repeats" in content
        assert "warmup" in content

    def test_compute_tflops_causal_parameter(self):
        """compute_tflops must accept causal param with 0.5 multiplier."""
        content = self._read_file(self._root("benchmarks", "utils.py"))
        if not content:
            pytest.skip("utils.py not found")
        assert "def compute_tflops" in content
        assert "causal" in content
        assert "0.5" in content

    def test_cuda_skip_guards(self):
        """Test file must have importorskip and CUDA availability guard."""
        content = self._read_file(self._root("tests", "test_flash_attn_correctness.py"))
        if not content:
            pytest.skip("test_flash_attn_correctness.py not found")
        assert "importorskip" in content or "flash_attn" in content
        assert "cuda" in content.lower()

    def test_varlen_uses_cu_seqlens(self):
        """test_varlen_attention.py must use cu_seqlens."""
        content = self._read_file(self._root("tests", "test_varlen_attention.py"))
        if not content:
            pytest.skip("test_varlen_attention.py not found")
        assert "cu_seqlens" in content

    # ── functional_check ─────────────────────────────────────────────────

    def test_compute_tflops_positive(self):
        """compute_tflops(2,1024,8,64,10.0,False) must return positive."""
        try:
            sys.path.insert(0, self.REPO_DIR)
            from benchmarks.utils import compute_tflops
        except ImportError:
            pytest.skip("Cannot import compute_tflops")
        result = compute_tflops(2, 1024, 8, 64, 10.0, False)
        assert result > 0

    def test_compute_tflops_causal_half(self):
        """Causal tflops must be ~0.5 * non-causal."""
        try:
            sys.path.insert(0, self.REPO_DIR)
            from benchmarks.utils import compute_tflops
        except ImportError:
            pytest.skip("Cannot import compute_tflops")
        non_causal = compute_tflops(2, 1024, 8, 64, 10.0, False)
        causal = compute_tflops(2, 1024, 8, 64, 10.0, True)
        assert causal == pytest.approx(non_causal * 0.5, rel=1e-6)

    def test_output_shape_assertion_in_test(self):
        """test_flash_attn_shapes.py must assert output.shape."""
        content = self._read_file(self._root("tests", "test_flash_attn_shapes.py"))
        if not content:
            pytest.skip("test_flash_attn_shapes.py not found")
        assert "output.shape" in content or "shape" in content
        assert "batch_size" in content or "seq_len" in content

    def test_oom_caught_in_benchmark(self):
        """benchmark_flash_attention.py must catch OutOfMemoryError."""
        content = self._read_file(self._root("benchmarks", "benchmark_flash_attention.py"))
        if not content:
            pytest.skip("benchmark_flash_attention.py not found")
        assert "OutOfMemoryError" in content or "MemoryError" in content
        assert "continue" in content or "skip" in content.lower()
