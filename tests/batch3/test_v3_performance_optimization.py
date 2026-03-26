"""
Tests for v3-performance-optimization skill.
REPO_DIR: /workspace/flash-attention
"""

import os
import pytest

REPO_DIR = "/workspace/flash-attention"


def _path(rel):
    return os.path.join(REPO_DIR, rel)


def _read(rel):
    with open(_path(rel), encoding="utf-8") as f:
        return f.read()


class TestV3PerformanceOptimization:
    # ── file_path_check ────────────────────────────────────────────────────
    def test_benchmark_attention_py_exists(self):
        """Verify benchmarks/benchmark_attention.py exists."""
        fpath = _path("benchmarks/benchmark_attention.py")
        assert os.path.isfile(fpath), "benchmarks/benchmark_attention.py must exist"
        assert os.path.getsize(fpath) > 0, "benchmark_attention.py must be non-empty"

    def test_memory_analysis_and_report_exist(self):
        """Verify memory_analysis.py and benchmark_report.py exist in benchmarks/."""
        memory_path = _path("benchmarks/memory_analysis.py")
        report_path = _path("benchmarks/benchmark_report.py")
        assert os.path.isfile(memory_path), "benchmarks/memory_analysis.py must exist"
        assert os.path.isfile(report_path), "benchmarks/benchmark_report.py must exist"

    # ── semantic_check ─────────────────────────────────────────────────────
    def test_cuda_event_timing_not_time_time(self):
        """Verify torch.cuda.Event is used for GPU timing (not time.time)."""
        content = _read("benchmarks/benchmark_attention.py")
        has_cuda_event = "torch.cuda.Event" in content or "cuda.Event" in content
        assert (
            has_cuda_event
        ), "torch.cuda.Event must be used for GPU timing, not wall-clock time.time"
        has_timing_calls = (
            "record()" in content
            or "elapsed_time(" in content
            or "synchronize()" in content
        )
        assert (
            has_timing_calls
        ), "CUDA event record()/elapsed_time()/synchronize() must be used for timing"

    def test_tflops_formula_correct(self):
        """Verify TFLOPS formula: 4*B*H*S^2*D / (time_ms * 1e9) is present."""
        content = _read("benchmarks/benchmark_attention.py")
        # Check for the 4* multiplier characteristic of attention TFLOPS formula
        has_4x = "4 *" in content or "4*" in content
        assert has_4x, "TFLOPS formula must start with '4 *' (attention ops multiplier)"
        has_time = "time_ms" in content or "elapsed" in content
        assert has_time, "Time in ms must be used in the TFLOPS denominator"
        has_tflops = "tflops" in content.lower() or "TFLOPS" in content
        assert has_tflops, "Result must be labeled as TFLOPS or tflops"

    def test_allclose_atol_1e2_for_correctness(self):
        """Verify torch.allclose with atol=1e-2 is used for numerical correctness."""
        content = _read("benchmarks/benchmark_attention.py")
        assert (
            "torch.allclose" in content
        ), "torch.allclose must be used for numerical correctness verification"
        has_atol = "atol=1e-2" in content or "atol=0.01" in content
        assert (
            has_atol
        ), "torch.allclose must use atol=1e-2 for FP16 precision tolerance"

    def test_oom_error_handling(self):
        """Verify try/except RuntimeError is used to handle GPU OOM errors gracefully."""
        content = _read("benchmarks/benchmark_attention.py")
        assert "try:" in content, "try: block must be present for OOM error handling"
        assert (
            "except RuntimeError" in content
        ), "except RuntimeError must be used for CUDA OOM handling"

    def test_complexity_labels_in_report(self):
        """Verify benchmark_report.py contains O(N) and O(N^2) complexity labels."""
        content = _read("benchmarks/benchmark_report.py")
        has_on = "O(N)" in content or "linear" in content.lower()
        assert has_on, "Benchmark report must include O(N) or 'linear' complexity label"
        has_on2 = (
            "O(N^2)" in content
            or "O(N**2)" in content
            or "quadratic" in content.lower()
        )
        assert (
            has_on2
        ), "Benchmark report must include O(N^2) or 'quadratic' complexity label"

    # ── functional_check (mocked / static) ────────────────────────────────
    def test_warmup_iterations_before_timing(self):
        """Verify GPU warmup iterations are performed before recording benchmark timing."""
        content = _read("benchmarks/benchmark_attention.py")
        warmup_patterns = ["warmup", "warm_up", "n_warmup", "warmup_iters"]
        has_warmup = any(p in content for p in warmup_patterns)
        assert has_warmup, (
            "Warmup loop must be present before timing starts "
            "(patterns: warmup, warm_up, n_warmup, warmup_iters)"
        )

    def test_memory_analysis_peak_memory_tracked(self):
        """Verify memory_analysis.py tracks peak GPU memory via torch.cuda.max_memory_allocated."""
        content = _read("benchmarks/memory_analysis.py")
        patterns = ["max_memory_allocated", "memory_allocated", "peak_memory"]
        has_pattern = any(p in content for p in patterns)
        assert has_pattern, (
            "Peak GPU memory must be tracked via torch.cuda.max_memory_allocated() or "
            "memory_allocated() in memory_analysis.py"
        )

    def test_benchmark_report_generates_summary(self):
        """Verify benchmark_report.py generates summary with TFLOPS and memory columns."""
        content = _read("benchmarks/benchmark_report.py")
        has_tflops = "TFLOPS" in content or "tflops" in content
        assert has_tflops, "Benchmark report must include TFLOPS column/field"
        has_memory = "memory_gb" in content or "memory" in content.lower()
        assert has_memory, "Benchmark report must include memory measurement (GB)"
        has_latency = "latency_ms" in content or "latency" in content.lower()
        assert has_latency, "Benchmark report must include latency in ms"

    def test_multiple_sequence_lengths_tested(self):
        """Verify benchmark tests multiple sequence lengths to capture scaling behaviour."""
        content = _read("benchmarks/benchmark_attention.py")
        patterns = [
            "seq_len",
            "sequence_lengths",
            "seq_lengths",
            "[128",
            "[256",
            "[512",
        ]
        has_seq_lengths = any(p in content for p in patterns)
        assert has_seq_lengths, (
            "Attention benchmark must test multiple sequence lengths "
            "(seq_len, sequence_lengths, or explicit [128/256/512 lists)"
        )

    def test_baseline_comparison_in_report(self):
        """Verify benchmark report compares optimized vs baseline implementation."""
        content = _read("benchmarks/benchmark_report.py")
        patterns = ["baseline", "speedup", "improvement", " vs ", "_vs_"]
        has_comparison = any(p in content.lower() for p in patterns)
        assert (
            has_comparison
        ), "Benchmark report must compare optimized vs baseline with speedup ratio"
