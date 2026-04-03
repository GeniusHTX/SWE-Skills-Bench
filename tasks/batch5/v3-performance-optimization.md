# Task: Benchmark and Optimize Flash Attention Forward Pass for Long Sequences

## Background

The flash-attention repository (https://github.com/Dao-AILab/flash-attention) implements memory-efficient attention kernels. For sequences longer than 4096 tokens with head dimension 128, the current v3 forward pass does not fully exploit shared memory tiling on Hopper (SM90) GPUs. This task requires benchmarking the existing implementation, identifying bottlenecks in tile scheduling and memory access patterns, and applying targeted optimizations to achieve measurable speedup and memory reduction.

## Files to Create/Modify

- `benchmarks/benchmark_flash_attn_long_seq.py` (create) — Benchmark script that measures forward-pass wall time and peak memory for sequence lengths [4096, 8192, 16384] with head_dim=128, num_heads=32, batch_size=[1, 4, 8], causal and non-causal.
- `hopper/flash_attn_interface.py` (modify) — Adjust tile-size selection logic for sequence lengths > 4096 to use larger tiles when shared memory permits.
- `hopper/flash_fwd_kernel.h` (modify) — Optimize the forward kernel's shared memory layout and pipeline staging for the long-sequence regime.
- `benchmarks/results/long_seq_baseline.csv` (create) — Baseline benchmark results captured before optimization.
- `benchmarks/results/long_seq_optimized.csv` (create) — Post-optimization benchmark results for comparison.

## Requirements

### Benchmark Script

- Must measure wall-clock time (median of 10 runs after 3 warmup runs) and peak GPU memory allocation for each configuration.
- Configurations: `seq_len ∈ {4096, 8192, 16384}`, `head_dim = 128`, `num_heads = 32`, `batch_size ∈ {1, 4, 8}`, `causal ∈ {True, False}`.
- Output results as CSV with columns: `seq_len`, `batch_size`, `causal`, `time_ms`, `peak_memory_mb`, `tflops`.
- Validate correctness by comparing outputs against `torch.nn.functional.scaled_dot_product_attention` with a tolerance of `atol=1e-2, rtol=1e-2`.

### Performance Targets

- Achieve at least 1.3× speedup (wall-clock time) for `seq_len=16384, batch_size=4, causal=True` compared to the unmodified baseline.
- Reduce peak memory usage by at least 10% for `seq_len=16384, batch_size=8, non-causal` compared to baseline.
- No accuracy regression: maximum absolute error vs. reference attention must remain below `1e-2` for `float16` inputs.

### Kernel Modifications

- The tile-size selection in `flash_attn_interface.py` must pick block sizes that maximize shared memory occupancy for `head_dim=128` and long sequences.
- The forward kernel pipeline must not introduce new synchronization barriers that would negate throughput gains.
- Changes must not break the backward pass or any existing shorter-sequence behavior.

### Expected Functionality

- Running `python benchmarks/benchmark_flash_attn_long_seq.py` produces both CSV files (baseline first run, optimized after changes) and prints a summary table with speedup ratios.
- `flash_attn_func(q, k, v, causal=True)` with `seq_len=16384` returns numerically correct output matching the reference within tolerance.
- `flash_attn_func` with `seq_len=512` (short sequence) still works correctly and does not regress in speed.

## Acceptance Criteria

- Baseline and optimized CSV benchmark results are present and show measurable improvement.
- The forward-pass kernel achieves ≥ 1.3× speedup for `seq_len=16384, batch_size=4, causal=True`.
- Peak memory is reduced by ≥ 10% for `seq_len=16384, batch_size=8, non-causal`.
- Numerical correctness is maintained: max absolute error < `1e-2` against the PyTorch reference for all configurations.
- `pip install -e .` and `python -c 'import flash_attn'` succeed without errors.
- Short-sequence behavior (seq_len ≤ 2048) is not regressed.
