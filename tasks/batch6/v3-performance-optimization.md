# Task: Optimize Flash Attention Forward Pass with Tiled Causal Masking and Memory-Efficient Benchmarking

## Background

The Flash Attention library (https://github.com/Dao-AILab/flash-attention) provides memory-efficient attention implementations. The current causal masking path in the forward pass kernel has sub-optimal performance for medium sequence lengths (512–2048) and lacks a dedicated benchmark suite to validate performance targets. The goal is to optimize the causal attention forward kernel and build a benchmark harness that measures speedup over the baseline implementation and tracks memory reduction.

## Files to Create/Modify

- `flash_attn/flash_attn_triton.py` (create) — A Triton-based reference implementation of the causal flash attention forward pass with tiled masking optimization
- `benchmarks/benchmark_causal.py` (create) — Benchmark script comparing baseline vs. optimized causal attention across sequence lengths (512, 1024, 2048, 4096) and head dimensions (64, 128)
- `benchmarks/benchmark_memory.py` (create) — Memory profiling script measuring peak GPU memory usage for standard attention vs. flash attention at various batch/sequence configurations
- `flash_attn/utils/benchmark_utils.py` (create) — Shared utilities for timing GPU operations (CUDA event timers, warmup loops, statistical summary)
- `tests/test_causal_correctness.py` (create) — Numerical correctness tests verifying the optimized causal kernel matches a naive PyTorch implementation within `atol=1e-3` for fp16

## Requirements

### Tiled Causal Masking Kernel

- Implement a Triton kernel for the forward pass of scaled dot-product attention with causal masking.
- The kernel must process queries and keys in tiles (block sizes of 64 and 128 must both be supported).
- Causal masking must be applied within the tiling loop by skipping fully-masked blocks and applying partial masks only to boundary tiles, avoiding a full `N×N` mask matrix allocation.
- The kernel must accept inputs of shape `(batch, nheads, seqlen, headdim)` and produce output of the same shape.
- The kernel must correctly handle non-power-of-two sequence lengths (e.g., 500, 1000, 1500).
- The kernel must support fp16 and bf16 dtypes.

### Benchmark Suite

- `benchmark_causal.py` must measure wall-clock time (in milliseconds) for the following configurations:
  - Sequence lengths: 512, 1024, 2048, 4096
  - Head dimensions: 64, 128
  - Batch size: 8, number of heads: 12
  - Data type: fp16
- Each configuration must be measured with at least 100 iterations after 10 warmup iterations.
- The script must report: median latency (ms), speedup ratio over `torch.nn.functional.scaled_dot_product_attention` with `is_causal=True`, and TFLOPS achieved.
- The script must output results in a machine-readable JSON format and a human-readable table printed to stdout.

### Memory Profiling

- `benchmark_memory.py` must measure peak GPU memory allocated (via `torch.cuda.max_memory_allocated`) for:
  - Standard attention (materializing the full `N×N` attention matrix)
  - Flash attention (the optimized kernel)
- Configurations: batch sizes [1, 4, 8], sequence lengths [1024, 2048, 4096], head_dim=64, nheads=12, dtype=fp16.
- The script must report memory usage in MB and compute the percentage reduction for each configuration.

### Correctness Tests

- Compare the output of the optimized causal kernel against `torch.matmul` + softmax + masking reference implementation.
- Test with random inputs at fp16 for at least 5 different `(batch, nheads, seqlen, headdim)` combinations.
- Absolute tolerance: `1e-3`, relative tolerance: `1e-2`.
- Verify that the output shape matches the input query shape exactly.
- Verify that positions above the causal diagonal receive zero attention weight.

### Expected Functionality

- Running `python benchmarks/benchmark_causal.py` → prints a table of latencies and speedups for all configurations, and writes `benchmark_causal_results.json`.
- Running `python benchmarks/benchmark_memory.py` → prints a memory comparison table showing MB used and percentage reduction for each config.
- Running `pytest tests/test_causal_correctness.py` → all tests pass, confirming numerical equivalence with the reference implementation within tolerance.
- The optimized kernel at seqlen=2048, headdim=64 must be at least 2x faster than standard PyTorch attention with a full materialized mask.
- Peak GPU memory at seqlen=4096 must be at least 50% lower than a naive full-matrix attention implementation.

## Acceptance Criteria

- A Triton kernel implements tiled causal attention that skips fully-masked blocks during the tiling loop rather than materializing a full N×N mask.
- The benchmark suite covers at least 8 distinct (seqlen × headdim) configurations and outputs structured JSON results.
- The memory profiling script demonstrates measurable memory reduction compared to standard attention at seqlen ≥ 1024.
- All correctness tests pass with the specified tolerances for fp16 inputs across multiple input shapes.
- Both fp16 and bf16 input dtypes are supported by the kernel without runtime errors.
- Non-power-of-two sequence lengths are handled correctly without out-of-bounds access or incorrect results.
- The project installs and imports successfully with `pip install -e . && python -c 'import flash_attn'`.
