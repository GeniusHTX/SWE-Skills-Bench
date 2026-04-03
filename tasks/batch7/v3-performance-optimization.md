# Task: Add a Flash Attention Benchmark Suite to flash-attention

## Background

The flash-attention library (https://github.com/Dao-AILab/flash-attention) provides CUDA-optimized attention kernels. The task is to implement a Python benchmark module that measures forward and backward pass throughput (TFLOPs/s) and memory usage for FlashAttention-2 versus standard PyTorch attention across multiple sequence lengths and batch sizes, and verifies that the measured speedup meets the expected 2x–7x range.

## Files to Create/Modify

- `benchmarks/benchmark_flash_attn_v2.py` (create) — Benchmark script that measures FlashAttention-2 vs standard attention throughput and memory usage
- `benchmarks/benchmark_utils.py` (create) — Shared utilities: TFLOP calculation, memory measurement, result formatting
- `tests/test_benchmark_correctness.py` (create) — Unit tests verifying benchmark utility functions and reporting format

## Requirements

### Benchmark Utilities (`benchmark_utils.py`)

```python
import torch
import time
from dataclasses import dataclass
from typing import Optional

@dataclass
class BenchmarkResult:
    name: str
    batch_size: int
    seq_len: int
    num_heads: int
    head_dim: int
    tflops: float                   # Teraflops per second (forward pass)
    backward_tflops: Optional[float]  # TFLOPs/s for backward pass (None if not measured)
    memory_mb: float                # Peak GPU memory used in MB
    latency_ms: float               # Average latency per iteration in ms
    dtype: str                      # "fp16" or "bf16"

def compute_attention_tflops(
    batch_size: int,
    seq_len: int,
    num_heads: int,
    head_dim: int,
    causal: bool,
    elapsed_seconds: float,
) -> float:
    """
    Compute TFLOPs/s for attention.
    
    For non-causal attention:
        FLOPs = 4 * batch_size * num_heads * seq_len^2 * head_dim
    For causal attention (triangular mask):
        FLOPs = 2 * batch_size * num_heads * seq_len^2 * head_dim
    
    TFLOPs/s = FLOPs / elapsed_seconds / 1e12
    """

def measure_peak_memory_mb(func, *args, **kwargs) -> tuple[float, any]:
    """
    Run `func(*args, **kwargs)` and measure peak GPU memory allocated.
    Returns (peak_memory_mb, return_value).
    Uses torch.cuda.reset_peak_memory_stats() before and torch.cuda.max_memory_allocated() after.
    """

def benchmark_forward(
    func,
    q: torch.Tensor,
    k: torch.Tensor,
    v: torch.Tensor,
    warmup_iters: int = 5,
    benchmark_iters: int = 50,
    **kwargs,
) -> tuple[float, float]:
    """
    Warm up with warmup_iters, then time benchmark_iters forward passes.
    Returns (avg_latency_ms, tflops_per_second).
    Uses torch.cuda.synchronize() before and after timing.
    """
```

### Main Benchmark Script (`benchmark_flash_attn_v2.py`)

#### Configuration

```python
BENCHMARK_CONFIGS = [
    # (batch_size, seq_len, num_heads, head_dim)
    (4,   512,  16, 64),
    (4,  1024,  16, 64),
    (2,  2048,  16, 64),
    (1,  4096,  16, 64),
    (1,  8192,  16, 64),
    (1, 16384,  16, 64),
]

DTYPES = [torch.float16, torch.bfloat16]
CAUSAL_OPTIONS = [False, True]
```

#### `benchmark_flash_attention(batch, seq, heads, dim, dtype, causal)` → `BenchmarkResult`

1. Create random `q, k, v` tensors of shape `(batch, seq, heads, dim)` with `dtype` on CUDA
2. Set `q.requires_grad_(True)`, same for `k` and `v`
3. Benchmark standard attention (reference):
   - Reshape to `(batch, heads, seq, dim)` for `torch.nn.functional.scaled_dot_product_attention`
   - Use `attn_mask` for causal: `is_causal=causal` parameter
4. Benchmark FlashAttention-2:
   - Use `flash_attn.flash_attn_func(q, k, v, causal=causal)`
5. Use `benchmark_forward` for each and `measure_peak_memory_mb`
6. Return a `BenchmarkResult` for each

#### `run_all_benchmarks()` → `list[tuple[BenchmarkResult, BenchmarkResult]]`

For each config in `BENCHMARK_CONFIGS`, each dtype in `DTYPES`, and each causal in `CAUSAL_OPTIONS`:
- Run `benchmark_flash_attention` for standard and flash attention
- Collect `(standard_result, flash_result)` pairs

#### `print_comparison_table(results)` Output Format

```
Flash Attention v2 Benchmark Results
═══════════════════════════════════════════════════════════════════════════
Config                          │ Standard Attn  │ Flash Attn v2  │ Speedup │ Memory Savings
──────────────────────────────────────────────────────────────────────────
bs=4 seq=512  h=16 d=64  fp16   │  45.2 TFLOPs/s │  98.3 TFLOPs/s │  2.18x  │  45.2%
bs=4 seq=1024 h=16 d=64  fp16   │  38.1 TFLOPs/s │ 167.4 TFLOPs/s │  4.39x  │  62.1%
...

Speedup range: min=2.18x max=7.12x avg=3.94x
Memory reduction range: 38.4% – 75.3%
```

- `Speedup = flash_result.tflops / standard_result.tflops`
- `Memory Savings = (standard_result.memory_mb - flash_result.memory_mb) / standard_result.memory_mb * 100`

#### speedup validation

After running all benchmarks, the script must assert (with a clear error message if failed):
```python
speedups = [flash.tflops / std.tflops for std, flash in results]
assert min(speedups) >= 1.5, f"Minimum speedup {min(speedups):.2f}x below expected 1.5x"
assert max(speedups) >= 2.0, f"Maximum speedup {max(speedups):.2f}x below expected 2.0x"
```

### Unit Tests (`tests/test_benchmark_correctness.py`)

Test the utility functions (CPU, not requiring GPU for CI):

1. **`test_compute_attention_tflops_noncausal`**: With `batch=1, seq=512, heads=8, dim=64, causal=False, elapsed=1.0s` — verify FLOPs = `4 * 1 * 8 * 512^2 * 64 = 536,870,912` → TFLOPs/s ≈ 5.37e-4

2. **`test_compute_attention_tflops_causal`**: Causal should return half the TFLOPs of non-causal (same inputs)

3. **`test_benchmark_result_dtype_field`**: `BenchmarkResult` `dtype` field is correctly set to `"fp16"` for `torch.float16`

4. **`test_print_comparison_table_format`**: Given two mock `BenchmarkResult` objects, `print_comparison_table` produces output containing the speedup value

## Expected Functionality

- `compute_attention_tflops` correctly applies the factor-of-2 for causal vs non-causal
- `measure_peak_memory_mb` returns a positive float and the correct function return value
- `benchmark_forward` uses CUDA synchronization for accurate timing
- For `seq_len=4096`, FlashAttention achieves at least 2x speedup over standard attention

## Acceptance Criteria

- `compute_attention_tflops` returns correct values for both causal and non-causal cases
- `benchmark_forward` runs warmup_iters before timing and uses `torch.cuda.synchronize()` around the timed loop
- `measure_peak_memory_mb` calls `reset_peak_memory_stats()` before and reads `max_memory_allocated()` after
- All benchmark configurations in `BENCHMARK_CONFIGS` are exercised in `run_all_benchmarks()`
- Speedup assertion validates minimum 1.5x and maximum 2.0x+ using `assert` with descriptive error messages
- `print_comparison_table` output includes speedup and memory savings columns
- `pip install -e . && python -c 'import flash_attn'` succeeds
- All unit tests pass without requiring a GPU (mock the GPU operations where needed)
