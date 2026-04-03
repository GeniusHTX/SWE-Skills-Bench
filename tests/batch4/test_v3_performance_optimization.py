"""
Test for 'v3-performance-optimization' skill — Performance Optimization
Validates AttentionBenchmark, SearchBenchmark, and memory benchmarking
utilities in the flash-attention repo.
"""

import os
import sys
import ast
import glob
import pytest


class TestV3PerformanceOptimization:
    """Tests for performance optimization in the flash-attention repo."""

    REPO_DIR = "/workspace/flash-attention"

    def _read(self, relpath):
        path = os.path.join(self.REPO_DIR, relpath)
        with open(path, "r", errors="ignore") as f:
            return f.read()

    def _find_benchmark_dir(self):
        candidates = [
            os.path.join(self.REPO_DIR, "benchmarks"),
            os.path.join(self.REPO_DIR, "benchmark"),
        ]
        for c in candidates:
            if os.path.isdir(c):
                return c
        # Fallback search
        matches = glob.glob(
            os.path.join(self.REPO_DIR, "**/benchmarks"), recursive=True
        )
        return matches[0] if matches else candidates[0]

    def _ensure_path(self):
        bdir = self._find_benchmark_dir()
        if bdir not in sys.path:
            sys.path.insert(0, bdir)

    # --- File Path Checks ---

    def test_benchmarks_dir_exists(self):
        """Verifies benchmarks directory exists."""
        bdir = self._find_benchmark_dir()
        assert os.path.isdir(bdir), f"Expected directory not found: {bdir}"

    def test_attention_benchmark_exists(self):
        """Verifies attention_benchmark.py exists."""
        bdir = self._find_benchmark_dir()
        path = os.path.join(bdir, "attention_benchmark.py")
        assert os.path.exists(path), f"Expected file not found: {path}"

    def test_search_benchmark_exists(self):
        """Verifies search_benchmark.py exists."""
        bdir = self._find_benchmark_dir()
        path = os.path.join(bdir, "search_benchmark.py")
        assert os.path.exists(path), f"Expected file not found: {path}"

    def test_memory_benchmark_exists(self):
        """Verifies memory_benchmark.py exists."""
        bdir = self._find_benchmark_dir()
        path = os.path.join(bdir, "memory_benchmark.py")
        assert os.path.exists(path), f"Expected file not found: {path}"

    # --- Semantic Checks (AST) ---

    def test_sem_attention_benchmark_class(self):
        """attention_benchmark.py defines AttentionBenchmark class."""
        bdir = self._find_benchmark_dir()
        src = self._read(
            os.path.relpath(os.path.join(bdir, "attention_benchmark.py"), self.REPO_DIR)
        )
        tree = ast.parse(src)
        classes = [n.name for n in ast.walk(tree) if isinstance(n, ast.ClassDef)]
        assert "AttentionBenchmark" in classes, "AttentionBenchmark class not found"

    def test_sem_attention_functions(self):
        """attention_benchmark.py defines standard_attention, flash_attention, benchmark_attention."""
        bdir = self._find_benchmark_dir()
        src = self._read(
            os.path.relpath(os.path.join(bdir, "attention_benchmark.py"), self.REPO_DIR)
        )
        tree = ast.parse(src)
        funcs = [n.name for n in ast.walk(tree) if isinstance(n, ast.FunctionDef)]
        for fn in ("standard_attention", "flash_attention", "benchmark_attention"):
            assert fn in funcs, f"Function {fn} not found in attention_benchmark.py"

    def test_sem_search_benchmark_class(self):
        """search_benchmark.py defines SearchBenchmark class."""
        bdir = self._find_benchmark_dir()
        src = self._read(
            os.path.relpath(os.path.join(bdir, "search_benchmark.py"), self.REPO_DIR)
        )
        tree = ast.parse(src)
        classes = [n.name for n in ast.walk(tree) if isinstance(n, ast.ClassDef)]
        assert "SearchBenchmark" in classes, "SearchBenchmark class not found"

    # --- Functional Checks ---

    def test_func_import_attention_benchmark(self):
        """AttentionBenchmark can be imported."""
        self._ensure_path()
        from attention_benchmark import AttentionBenchmark

        assert AttentionBenchmark is not None

    def test_func_import_torch(self):
        """torch is available for benchmarking."""
        import torch

        assert torch is not None

    def test_func_attention_benchmark_construct(self):
        """AttentionBenchmark can be constructed with cpu and float32."""
        self._ensure_path()
        import torch
        from attention_benchmark import AttentionBenchmark

        bm = AttentionBenchmark(device="cpu", dtype=torch.float32)
        assert bm is not None

    def test_func_standard_attention_output_shape(self):
        """standard_attention output shape matches (B, H, S, D)."""
        self._ensure_path()
        import torch
        from attention_benchmark import AttentionBenchmark

        bm = AttentionBenchmark(device="cpu", dtype=torch.float32)
        B, H, S, D = 1, 2, 32, 16
        q = torch.randn(B, H, S, D)
        k = torch.randn(B, H, S, D)
        v = torch.randn(B, H, S, D)
        out = bm.standard_attention(q, k, v)
        assert out.shape == (
            B,
            H,
            S,
            D,
        ), f"Expected shape {(B, H, S, D)}, got {out.shape}"

    def test_func_benchmark_attention_results(self):
        """benchmark_attention returns results for each sequence length."""
        self._ensure_path()
        import torch
        from attention_benchmark import AttentionBenchmark

        bm = AttentionBenchmark(device="cpu", dtype=torch.float32)
        seq_lengths = [32, 64]
        results = bm.benchmark_attention(
            batch_size=1,
            num_heads=2,
            seq_lengths=seq_lengths,
            head_dim=16,
            num_runs=3,
        )
        assert isinstance(results, (list, dict))
        if isinstance(results, list):
            assert len(results) == len(seq_lengths)
        else:
            assert len(results) >= len(seq_lengths)

    def test_func_benchmark_results_have_timing(self):
        """benchmark_attention results include timing information."""
        self._ensure_path()
        import torch
        from attention_benchmark import AttentionBenchmark

        bm = AttentionBenchmark(device="cpu", dtype=torch.float32)
        results = bm.benchmark_attention(
            batch_size=1,
            num_heads=2,
            seq_lengths=[32],
            head_dim=16,
            num_runs=3,
        )
        if isinstance(results, list):
            r = results[0]
        else:
            r = list(results.values())[0]
        # Should have timing info (mean, median, or time)
        assert any(
            k in str(r).lower() for k in ("mean", "median", "time", "ms", "sec")
        ), f"No timing info in result: {r}"

    def test_func_search_benchmark_construct(self):
        """SearchBenchmark can be constructed."""
        self._ensure_path()
        from search_benchmark import SearchBenchmark

        sb = SearchBenchmark()
        assert sb is not None

    def test_func_attention_benchmark_num_runs(self):
        """benchmark_attention respects num_runs parameter."""
        self._ensure_path()
        import torch
        from attention_benchmark import AttentionBenchmark

        bm = AttentionBenchmark(device="cpu", dtype=torch.float32)
        # Smoke test: should not raise for num_runs=1
        results = bm.benchmark_attention(
            batch_size=1,
            num_heads=1,
            seq_lengths=[16],
            head_dim=8,
            num_runs=1,
        )
        assert results is not None

    def test_func_attention_output_values_finite(self):
        """standard_attention output values are all finite."""
        self._ensure_path()
        import torch
        from attention_benchmark import AttentionBenchmark

        bm = AttentionBenchmark(device="cpu", dtype=torch.float32)
        q = torch.randn(1, 1, 16, 8)
        k = torch.randn(1, 1, 16, 8)
        v = torch.randn(1, 1, 16, 8)
        out = bm.standard_attention(q, k, v)
        assert torch.isfinite(out).all(), "Output contains non-finite values"
