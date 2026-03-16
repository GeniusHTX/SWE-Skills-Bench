"""
Test for 'v3-performance-optimization' skill — Flash Attention Performance
Validates that the Agent implemented or optimized performance benchmarks
and kernel configurations in the flash-attention project.
"""

import os
import subprocess
import pytest


class TestV3PerformanceOptimization:
    """Verify flash-attention performance optimization."""

    REPO_DIR = "/workspace/flash-attention"

    # ------------------------------------------------------------------
    # L1: file existence
    # ------------------------------------------------------------------

    def test_benchmark_file_exists(self):
        """A benchmark or performance test file must exist."""
        found = []
        for root, dirs, files in os.walk(self.REPO_DIR):
            for f in files:
                if ("bench" in f.lower() or "perf" in f.lower()) and f.endswith(
                    (".py", ".cu", ".cuh")
                ):
                    found.append(os.path.join(root, f))
        assert len(found) >= 1, "No benchmark/perf file found"

    def test_config_or_readme_exists(self):
        """Documentation for optimization must exist."""
        found = []
        for root, dirs, files in os.walk(self.REPO_DIR):
            for f in files:
                if f.lower() in ("readme.md", "benchmark.md") or (
                    "optim" in f.lower() and f.endswith(".md")
                ):
                    found.append(os.path.join(root, f))
        assert len(found) >= 1, "No optimization documentation found"

    # ------------------------------------------------------------------
    # L2: content validation
    # ------------------------------------------------------------------

    def _find_perf_files(self):
        found = []
        for root, dirs, files in os.walk(self.REPO_DIR):
            for f in files:
                if f.endswith((".py", ".cu", ".cuh")) and "node_modules" not in root:
                    fpath = os.path.join(root, f)
                    try:
                        with open(fpath, "r", errors="ignore") as fh:
                            content = fh.read()
                        if any(
                            p in content.lower()
                            for p in [
                                "benchmark",
                                "flash_attn",
                                "attention",
                                "performance",
                                "kernel",
                            ]
                        ):
                            found.append(fpath)
                    except OSError:
                        pass
        return found

    def _read_all_perf(self):
        content = ""
        for fpath in self._find_perf_files():
            with open(fpath, "r", errors="ignore") as f:
                content += f.read() + "\n"
        return content

    def test_flash_attention_import(self):
        """Must reference flash_attn or attention implementation."""
        content = self._read_all_perf()
        patterns = [
            "flash_attn",
            "flash_attention",
            "FlashAttention",
            "attention",
            "softmax",
        ]
        found = any(p in content for p in patterns)
        assert found, "No flash attention reference found"

    def test_timing_measurement(self):
        """Must measure execution time."""
        content = self._read_all_perf()
        timing_patterns = [
            "time.",
            "benchmark",
            "timer",
            "elapsed",
            "torch.cuda.synchronize",
            "Event",
            "perf_counter",
            "ms",
            "latency",
        ]
        found = any(p in content.lower() for p in timing_patterns)
        assert found, "No timing measurement found"

    def test_memory_profiling(self):
        """Must profile memory usage."""
        content = self._read_all_perf()
        mem_patterns = [
            "memory",
            "max_memory_allocated",
            "memory_reserved",
            "cuda.mem",
            "mem_efficient",
            "peak_memory",
            "FLOPS",
            "flops",
        ]
        found = any(p in content.lower() for p in mem_patterns)
        assert found, "No memory profiling found"

    def test_batch_size_variation(self):
        """Must test with varying batch/sequence sizes."""
        content = self._read_all_perf()
        size_patterns = [
            "batch_size",
            "seq_len",
            "seqlen",
            "head_dim",
            "num_heads",
            "d_model",
            "causal",
            "for .* in",
        ]
        found = sum(1 for p in size_patterns if p in content.lower())
        assert found >= 2, "Insufficient size variation in benchmarks"

    def test_comparison_baseline(self):
        """Must compare against baseline implementation."""
        content = self._read_all_perf()
        baseline_patterns = [
            "baseline",
            "standard",
            "vanilla",
            "reference",
            "naive",
            "comparison",
            "speedup",
            "vs",
            "pytorch",
        ]
        found = any(p in content.lower() for p in baseline_patterns)
        assert found, "No baseline comparison found"

    def test_cuda_or_torch(self):
        """Must use CUDA or PyTorch."""
        content = self._read_all_perf()
        cuda_patterns = [
            "torch",
            "cuda",
            "__global__",
            "cudaMalloc",
            "torch.cuda",
            "device",
            "GPU",
        ]
        found = any(p in content for p in cuda_patterns)
        assert found, "No CUDA/PyTorch usage found"

    def test_results_output(self):
        """Must output benchmark results."""
        content = self._read_all_perf()
        output_patterns = [
            "print",
            "log",
            "save",
            "write",
            "csv",
            "json",
            "table",
            "format",
        ]
        found = any(p in content.lower() for p in output_patterns)
        assert found, "No results output found"

    def test_python_scripts_compile(self):
        """Python benchmark files must compile."""
        for fpath in self._find_perf_files():
            if fpath.endswith(".py"):
                result = subprocess.run(
                    ["python", "-m", "py_compile", fpath],
                    capture_output=True,
                    text=True,
                    timeout=30,
                )
                assert (
                    result.returncode == 0
                ), f"{fpath} compile error:\n{result.stderr}"
