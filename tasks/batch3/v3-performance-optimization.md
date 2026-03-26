# Task: Implement Flash Attention Benchmark Suite with Memory Optimization Analysis

## Background

Flash Attention (https://github.com/Dao-AILab/flash-attention) is an efficient attention implementation that reduces memory usage and improves speed. The project needs a comprehensive benchmarking suite that measures attention computation performance across different configurations, compares Flash Attention against standard attention, and analyzes memory optimization characteristics including I/O complexity and memory bandwidth utilization.

## Files to Create/Modify

- `benchmarks/benchmark_attention.py` (create) — Benchmark suite comparing Flash Attention vs standard attention across configurations
- `benchmarks/memory_analysis.py` (create) — Memory usage analysis and optimization metrics
- `benchmarks/benchmark_report.py` (create) — Report generator with performance comparison tables and scaling analysis
- `tests/test_benchmark_suite.py` (create) — Tests for benchmark correctness and report generation

## Requirements

### Attention Benchmark Suite

- Implement a `AttentionBenchmark` class that measures performance of attention computations:
  - **Configurations to benchmark**: batch sizes [1, 4, 8, 16], sequence lengths [512, 1024, 2048, 4096, 8192], head dimensions [64, 128], number of heads [8, 16, 32]
  - **Implementations to compare**: Flash Attention (from `flash_attn`), PyTorch standard attention (`torch.nn.functional.scaled_dot_product_attention`), naive manual attention (Q @ K^T / sqrt(d) then softmax then @ V)
  - For each configuration, measure: wall-clock time (ms, averaged over 10 runs with 3 warmup), peak GPU memory (MB), TFLOPS achieved
- FLOPS calculation for attention: `4 * batch * heads * seq_len^2 * head_dim` (2 for QK^T matmul, 2 for softmax@V matmul)
- TFLOPS = FLOPS / (time_seconds * 10^12)
- Use CUDA events for precise GPU timing, not wall-clock time
- Skip configurations that would exceed available GPU memory (estimate before running: standard attention for seq_len 8192 with batch 16 requires ~16GB for the attention matrix)

### Memory Analysis

- Implement a `MemoryAnalyzer` class that tracks and reports memory characteristics:
  - **Peak memory usage**: measure `torch.cuda.max_memory_allocated()` before and after each benchmark
  - **Memory scaling**: plot how memory grows with sequence length for each implementation
  - Flash Attention theoretical: O(N) memory where N = seq_len
  - Standard attention theoretical: O(N^2) memory where N = seq_len (stores full attention matrix)
  - **Memory savings ratio**: `standard_peak_memory / flash_peak_memory` for each configuration
- Verify that Flash Attention memory growth is approximately linear with sequence length (within 20% of linear regression)
- Verify that standard attention memory growth is approximately quadratic with sequence length

### Correctness Verification

- Before benchmarking, verify that all implementations produce the same output:
  - Compute attention using all three methods on the same input tensors
  - Assert `torch.allclose(flash_output, standard_output, atol=1e-2, rtol=1e-2)` (FP16 tolerance)
  - Log the maximum absolute difference between implementations
- Support both FP16 and BF16 data types; verify correctness for each

### Benchmark Report

- Implement `BenchmarkReport` class that generates:
  - **Speedup table**: Flash Attention speedup over standard attention for each configuration (speedup = standard_time / flash_time)
  - **Memory savings table**: memory reduction percentage for each configuration
  - **Scaling analysis**: how speedup changes with increasing sequence length (the speedup should increase with longer sequences)
  - **Peak performance**: identify the configuration with highest TFLOPS
  - **Threshold analysis**: identify the minimum sequence length where Flash Attention outperforms standard attention
- Output formats: structured text tables, CSV, JSON (deterministic output)

### Configuration and Reproducibility

- Accept a YAML or dict configuration to specify which benchmarks to run
- Set random seeds for reproducibility: `torch.manual_seed(42)`, `torch.cuda.manual_seed(42)`
- Log GPU device name, CUDA version, and driver version at the start of each benchmark run
- Each benchmark result includes: timestamp, GPU info, configuration parameters, and all measured metrics

### Expected Functionality

- Benchmarking Flash Attention vs standard at seq_len=4096 shows Flash Attention is 2–5x faster
- Memory analysis shows Flash Attention uses ~10x less memory at seq_len=8192 compared to standard
- Speedup increases with longer sequence lengths (e.g., 2x at 512, 4x at 4096)
- Correctness check passes for all configurations within FP16 tolerance
- Configurations exceeding GPU memory are skipped gracefully with a logged warning
- The threshold analysis identifies that Flash Attention becomes faster than standard at approximately seq_len=256–512

## Acceptance Criteria

- Benchmark suite measures time, memory, and TFLOPS for all three attention implementations across specified configurations
- CUDA event timing is used for GPU measurements (not wall-clock)
- FLOPS calculation follows the formula `4 * batch * heads * seq_len^2 * head_dim`
- Memory analysis correctly tracks peak GPU memory and computes savings ratios
- Flash Attention memory growth is verified as approximately linear; standard attention as approximately quadratic
- Correctness verification using `torch.allclose` passes for all configurations in FP16 and BF16
- Benchmark report includes speedup tables, memory savings, scaling analysis, and peak performance identification
- Configurations exceeding GPU memory are detected and skipped without crashing
- Reports export to CSV and JSON with deterministic output
- Tests verify FLOPS calculations, report generation, and memory scaling verification logic with mock data
