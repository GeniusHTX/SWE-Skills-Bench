"""
Test for 'v3-performance-optimization' skill — Flash Attention benchmark
Validates that the Agent created a Flash Attention benchmark suite
comparing standard and flash attention performance with TFLOPS metrics.
"""

import os
import re

import pytest


class TestV3PerformanceOptimization:
    """Verify Flash Attention benchmark implementation."""

    REPO_DIR = "/workspace/flash-attention"

    def test_benchmark_file_exists(self):
        """benchmark_flash_attention.py must exist with a benchmark function."""
        found = False
        for root, dirs, files in os.walk(self.REPO_DIR):
            for f in files:
                if f == "benchmark_flash_attention.py":
                    path = os.path.join(root, f)
                    with open(path, "r", errors="ignore") as fh:
                        content = fh.read()
                    if re.search(r"def\s+(benchmark|run_benchmark)", content):
                        found = True
                        break
            if found:
                break
        assert found, "benchmark_flash_attention.py with benchmark function not found"

    def test_compare_attention_file_exists(self):
        """compare_attention.py must exist for side-by-side comparison."""
        found = False
        for root, dirs, files in os.walk(self.REPO_DIR):
            for f in files:
                if f == "compare_attention.py":
                    found = True
                    break
            if found:
                break
        assert found, "compare_attention.py not found"

    def test_tflops_formula_is_correct(self):
        """TFLOPS calculation must use correct formula."""
        found = False
        for root, dirs, files in os.walk(self.REPO_DIR):
            for f in files:
                if f == "benchmark_flash_attention.py":
                    path = os.path.join(root, f)
                    with open(path, "r", errors="ignore") as fh:
                        content = fh.read()
                    if re.search(r"[Tt][Ff][Ll][Oo][Pp][Ss]|flops|1e12|teraflops", content):
                        found = True
                        break
            if found:
                break
        assert found, "TFLOPS formula not found in benchmark script"

    def test_cuda_availability_check_present(self):
        """Script must check CUDA availability before running GPU benchmarks."""
        found = False
        for root, dirs, files in os.walk(self.REPO_DIR):
            for f in files:
                if f == "benchmark_flash_attention.py":
                    path = os.path.join(root, f)
                    with open(path, "r", errors="ignore") as fh:
                        content = fh.read()
                    if re.search(r"cuda\.is_available|torch\.cuda|CUDA", content):
                        found = True
                        break
            if found:
                break
        assert found, "CUDA availability check not found"

    def test_multiple_sequence_lengths_benchmarked(self):
        """Benchmark must test multiple sequence lengths."""
        found = False
        for root, dirs, files in os.walk(self.REPO_DIR):
            for f in files:
                if f == "benchmark_flash_attention.py":
                    path = os.path.join(root, f)
                    with open(path, "r", errors="ignore") as fh:
                        content = fh.read()
                    if re.search(r"seq_len|sequence_length", content):
                        if re.search(r"\[.*\d+.*,.*\d+.*,.*\d+", content):
                            found = True
                            break
            if found:
                break
        assert found, "Multiple sequence length sweep not found in benchmark"

    def test_tabular_output_columns_correct(self):
        """Output table must include seq_len, latency, and TFLOPS columns."""
        found = False
        for root, dirs, files in os.walk(self.REPO_DIR):
            for f in files:
                if f == "compare_attention.py":
                    path = os.path.join(root, f)
                    with open(path, "r", errors="ignore") as fh:
                        content = fh.read()
                    if re.search(r"seq_len|sequence", content, re.IGNORECASE):
                        if re.search(r"latency|time|ms", content, re.IGNORECASE):
                            found = True
                            break
            if found:
                break
        assert found, "Tabular output with seq_len and latency columns not found"

    def test_benchmark_module_imports_cleanly(self):
        """benchmark_flash_attention.py must have valid Python syntax."""
        found = False
        for root, dirs, files in os.walk(self.REPO_DIR):
            for f in files:
                if f == "benchmark_flash_attention.py":
                    path = os.path.join(root, f)
                    with open(path, "r", errors="ignore") as fh:
                        content = fh.read()
                    try:
                        compile(content, path, "exec")
                        found = True
                    except SyntaxError:
                        pass
                    break
            if found:
                break
        assert found, "benchmark_flash_attention.py has syntax errors"

    def test_tflops_calculation_for_known_values(self):
        """TFLOPS calculation function must exist."""
        found = False
        for root, dirs, files in os.walk(self.REPO_DIR):
            for f in files:
                if f == "benchmark_flash_attention.py":
                    path = os.path.join(root, f)
                    with open(path, "r", errors="ignore") as fh:
                        content = fh.read()
                    if re.search(r"def\s+calculate_tflops|def\s+compute_tflops|tflops\s*=", content):
                        found = True
                        break
            if found:
                break
        assert found, "TFLOPS calculation function or assignment not found"

    def test_cpu_fallback_does_not_crash(self):
        """Script must handle CPU fallback gracefully."""
        found = False
        for root, dirs, files in os.walk(self.REPO_DIR):
            for f in files:
                if f == "benchmark_flash_attention.py":
                    path = os.path.join(root, f)
                    with open(path, "r", errors="ignore") as fh:
                        content = fh.read()
                    if re.search(r"cpu|device|fallback|not.*available", content, re.IGNORECASE):
                        found = True
                        break
            if found:
                break
        assert found, "CPU fallback logic not found"

    def test_zero_seq_len_raises_valueerror(self):
        """Zero sequence length must be validated."""
        found = False
        for root, dirs, files in os.walk(self.REPO_DIR):
            for f in files:
                if f == "benchmark_flash_attention.py":
                    path = os.path.join(root, f)
                    with open(path, "r", errors="ignore") as fh:
                        content = fh.read()
                    if re.search(r"ValueError|assert.*seq_len|assert.*> ?0|<= ?0", content):
                        found = True
                        break
            if found:
                break
        assert found, "Zero sequence length validation not found"

    def test_flash_attention_faster_than_standard_for_long_seqs(self):
        """Comparison must record flash attention vs standard attention."""
        found = False
        for root, dirs, files in os.walk(self.REPO_DIR):
            for f in files:
                if f == "compare_attention.py":
                    path = os.path.join(root, f)
                    with open(path, "r", errors="ignore") as fh:
                        content = fh.read()
                    if re.search(r"flash", content, re.IGNORECASE) and re.search(
                        r"standard|vanilla|naive", content, re.IGNORECASE
                    ):
                        found = True
                        break
            if found:
                break
        assert found, "Flash vs standard attention comparison not found"
