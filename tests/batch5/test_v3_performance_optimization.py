"""
Test for 'v3-performance-optimization' skill — Flash Attention Performance
Validates speedup ratio, memory tracking, causal mask,
attention kernel, and performance benchmarking.
"""

import os
import re

import pytest


class TestV3PerformanceOptimization:
    """Verify Flash Attention performance optimizations."""

    REPO_DIR = "/workspace/flash-attention"

    # ── file_path_check ─────────────────────────────────────────────────────

    def test_repo_exists(self):
        """Verify flash-attention repository exists."""
        assert os.path.isdir(self.REPO_DIR), "flash-attention repo not found"

    def test_source_files_exist(self):
        """Verify CUDA/Python source files exist."""
        found = False
        for dirpath, _, fnames in os.walk(self.REPO_DIR):
            if ".git" in dirpath:
                continue
            for f in fnames:
                if f.endswith((".cu", ".cuh", ".py", ".cpp")):
                    found = True
                    break
            if found:
                break
        assert found, "No source files found"

    # ── semantic_check ──────────────────────────────────────────────────────

    def test_speedup_ratio(self):
        """Verify speedup ratio measurement or reference."""
        source_files = self._find_source_files()
        for fpath in source_files:
            content = self._read(fpath)
            if re.search(
                r"(speedup|speed_up|faster|ratio|benchmark|throughput)",
                content,
                re.IGNORECASE,
            ):
                return
        pytest.fail("No speedup ratio reference found")

    def test_memory_tracking(self):
        """Verify memory tracking/optimization."""
        source_files = self._find_source_files()
        for fpath in source_files:
            content = self._read(fpath)
            if re.search(
                r"(memory|mem_efficient|memory_efficient|peak_memory|max_memory_allocated)",
                content,
                re.IGNORECASE,
            ):
                return
        pytest.fail("No memory tracking found")

    def test_causal_mask(self):
        """Verify causal mask implementation."""
        source_files = self._find_source_files()
        for fpath in source_files:
            content = self._read(fpath)
            if re.search(
                r"(causal|is_causal|causal_mask|mask.*causal|triu)",
                content,
                re.IGNORECASE,
            ):
                return
        pytest.fail("No causal mask found")

    def test_attention_kernel(self):
        """Verify flash attention kernel implementation."""
        source_files = self._find_source_files()
        for fpath in source_files:
            content = self._read(fpath)
            if re.search(
                r"(flash.?attn|flash_attention|FlashAttention|attention.*kernel)",
                content,
                re.IGNORECASE,
            ):
                return
        pytest.fail("No flash attention kernel found")

    def test_tiling_or_blocking(self):
        """Verify tiling/blocking strategy for GPU."""
        source_files = self._find_source_files()
        for fpath in source_files:
            content = self._read(fpath)
            if re.search(
                r"(tile|block|BLOCK_SIZE|blockDim|tile_size|shared_mem)",
                content,
                re.IGNORECASE,
            ):
                return
        pytest.fail("No tiling/blocking strategy found")

    # ── functional_check ────────────────────────────────────────────────────

    def test_python_files_parse(self):
        """Verify Python source files are syntactically valid."""
        import ast

        py_files = [f for f in self._find_source_files() if f.endswith(".py")]
        for fpath in py_files[:15]:
            content = self._read(fpath)
            try:
                ast.parse(content, filename=fpath)
            except SyntaxError as e:
                pytest.fail(f"SyntaxError in {os.path.basename(fpath)}: {e}")

    def test_benchmark_script(self):
        """Verify benchmark or profiling script exists."""
        source_files = self._find_source_files()
        for fpath in source_files:
            basename = os.path.basename(fpath).lower()
            if "bench" in basename or "profile" in basename or "perf" in basename:
                return
            content = self._read(fpath)
            if re.search(
                r"(benchmark|time\.\w+|perf_counter|torch\.cuda\.Event)", content
            ):
                return
        pytest.fail("No benchmark script found")

    def test_softmax_computation(self):
        """Verify online/fused softmax computation."""
        source_files = self._find_source_files()
        for fpath in source_files:
            content = self._read(fpath)
            if re.search(
                r"(softmax|logsumexp|exp\(|online_softmax)", content, re.IGNORECASE
            ):
                return
        pytest.fail("No softmax computation found")

    def test_backward_pass(self):
        """Verify backward pass / gradient computation."""
        source_files = self._find_source_files()
        for fpath in source_files:
            content = self._read(fpath)
            if re.search(
                r"(backward|bwd|gradient|dout|dq|dk|dv|autograd)",
                content,
                re.IGNORECASE,
            ):
                return
        pytest.fail("No backward pass found")

    def test_dropout_support(self):
        """Verify dropout support in attention."""
        source_files = self._find_source_files()
        for fpath in source_files:
            content = self._read(fpath)
            if re.search(
                r"(dropout|drop_prob|p_drop|dropout_mask)", content, re.IGNORECASE
            ):
                return
        pytest.fail("No dropout support found")

    # ── helpers ──────────────────────────────────────────────────────────────

    def _find_source_files(self):
        results = []
        for dirpath, _, fnames in os.walk(self.REPO_DIR):
            if ".git" in dirpath:
                continue
            for f in fnames:
                if f.endswith((".py", ".cu", ".cuh", ".cpp", ".h")):
                    results.append(os.path.join(dirpath, f))
        return results

    def _read(self, path):
        with open(path, "r", errors="ignore") as fh:
            return fh.read()
