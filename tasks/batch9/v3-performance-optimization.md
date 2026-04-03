# Task: Add a Benchmark Suite and FlashAttention-3 Integration Test to flash-attention

## Background

Flash Attention (https://github.com/Dao-AILab/flash-attention) implements efficient attention algorithms. A new Python benchmark suite and integration test module is needed that measures FlashAttention-2/3 speedup versus standard PyTorch attention, validates numerical correctness, benchmarks memory bandwidth utilization, tests multi-head attention with different sequence lengths and head dimensions, and profiles the backward pass.

## Files to Create/Modify

- `benchmarks/benchmark_flash_attention.py` (create) — End-to-end benchmark comparing FlashAttention forward pass against PyTorch `F.scaled_dot_product_attention` across sequence lengths `[512, 1024, 2048, 4096, 8192]`
- `benchmarks/benchmark_backward.py` (create) — Backward pass benchmark measuring gradient computation time for both FlashAttention and standard attention
- `benchmarks/memory_efficiency.py` (create) — Memory footprint benchmark measuring peak GPU memory for both implementations across batch sizes
- `benchmarks/utils.py` (create) — Benchmark utilities: timing with CUDA events, memory measurement with `torch.cuda.max_memory_allocated`, warmup runs, and result formatting
- `tests/test_flash_attn_correctness.py` (create) — Numerical correctness tests: compare FlashAttention output against standard scaled dot-product attention with tolerances by dtype
- `tests/test_flash_attn_shapes.py` (create) — Shape and configuration tests: various head dimensions (32, 64, 128, 256), causal vs non-causal, different dtypes (fp16, bf16)
- `tests/test_varlen_attention.py` (create) — Variable-length sequence tests using `flash_attn_varlen_func` with packed sequences

## Requirements

### Benchmark Utilities (`benchmarks/utils.py`)

- Function `benchmark_forward(fn, *args, repeats=100, warmup=10) -> BenchmarkResult`:
  - `BenchmarkResult`: `mean_ms`, `std_ms`, `min_ms`, `max_ms`, `tflops`
  - Uses CUDA events for accurate timing: `start.record()`, `end.record()`, `torch.cuda.synchronize()`
  - Runs `warmup` iterations before timing
  - Returns statistics over `repeats` runs
- Function `benchmark_memory(fn, *args) -> int`:
  - Calls `torch.cuda.reset_peak_memory_stats()`
  - Runs `fn(*args)` once
  - Returns `torch.cuda.max_memory_allocated()` in bytes
- Function `compute_tflops(batch_size, seq_len, num_heads, head_dim, time_ms, causal=False) -> float`:
  - FLOPs for attention: `4 * batch_size * num_heads * seq_len^2 * head_dim` (non-causal)
  - For causal: multiply by 0.5 (only half the attention matrix)
  - `TFLOPS = FLOPs / (time_ms * 1e9)` (result in TeraFLOPS)
- Function `format_results(results: dict) -> str` — Pretty-print benchmark table with speedup ratios

### Forward Benchmark (`benchmarks/benchmark_flash_attention.py`)

- For each configuration in the outer product of:
  - `seq_lens = [512, 1024, 2048, 4096, 8192]`
  - `batch_size = 2`, `num_heads = 16`, `head_dim = 64`, `dtype = torch.float16`
  - `causal in [False, True]`
- Run:
  1. Standard attention: `F.scaled_dot_product_attention(q, k, v, is_causal=causal)`
  2. FlashAttention: `flash_attn_qkvpacked_func` or `flash_attn_func`
- Compute speedup: `standard_ms / flash_ms`
- Print table columns: seq_len, causal, standard(ms), flash(ms), speedup, flash_tflops
- Skip configurations where `seq_len * batch_size * num_heads * head_dim` exceeds GPU memory (catch OOM)
- Skip entire benchmark gracefully if `flash_attn` package is not importable

### Backward Benchmark (`benchmarks/benchmark_backward.py`)

- For each configuration, benchmark the backward pass:
  1. Create `q, k, v` with `requires_grad=True`
  2. Forward pass followed by `loss = out.mean(); loss.backward()`
  3. Time the full forward+backward round
- Compare FlashAttention backward vs standard attention backward
- Report: forward time, backward time, peak memory for each implementation

### Memory Efficiency Benchmark (`benchmarks/memory_efficiency.py`)

- Compare peak GPU memory usage for standard attention vs FlashAttention across:
  - `batch_sizes = [1, 4, 8]`
  - `seq_lens = [512, 1024, 2048, 4096]`
- For standard attention: memory scales as O(N²) per head (`batch * heads * seq² * 4 bytes`)
- Print table: batch, seq_len, standard_memory_mb, flash_memory_mb, memory_reduction_percent
- Verify that flash attention uses ≤ 40% of standard attention memory for seq_len ≥ 2048

### Correctness Tests (`tests/test_flash_attn_correctness.py`)

- Fixture `qkv_tensors(batch_size=2, seq_len=1024, num_heads=8, head_dim=64)` — Returns `(q, k, v)` in `torch.float16`
- `test_forward_correctness_fp16` — Compare `flash_attn_func(q, k, v)` vs `F.scaled_dot_product_attention(q, k, v)`:
  - `torch.testing.assert_close(flash_out, sdpa_out, atol=1e-3, rtol=1e-3)`
  - Cast both to float32 before comparison
- `test_forward_correctness_bf16` — Same test with `torch.bfloat16`, use `atol=2e-3, rtol=2e-3`
- `test_causal_mask_correctness` — Verify causal attention zeros out upper triangle: sample a few positions above the diagonal and check they don't influence the output
- `test_gradient_correctness` — Compare gradients: `torch.autograd.gradcheck` or manual comparison with `atol=1e-2`
- Skip all tests with `pytest.importorskip("flash_attn")` and skip on non-CUDA devices (`torch.cuda.is_available()`)

### Shape Tests (`tests/test_flash_attn_shapes.py`)

- `test_head_dimensions` — Test `head_dim in [32, 64, 128, 256]` all produce correct output shapes `(batch, seq, heads, head_dim)`
- `test_variable_batch_sizes` — Test `batch_size in [1, 2, 8, 16]` all work
- `test_various_dtypes` — Test fp16 and bf16 (skip fp32 as FlashAttention requires fp16/bf16)
- `test_output_shape` — Assert output shape matches `(batch_size, seq_len, num_heads, head_dim)`
- Skip unsupported head dimensions gracefully (some FA versions support only specific dims)

### Variable-Length Tests (`tests/test_varlen_attention.py`)

- `test_varlen_basic` — Create a packed batch of variable-length sequences:
  - 3 sequences of lengths [128, 256, 512]
  - Create `cu_seqlens = torch.tensor([0, 128, 384, 896])` (cumulative sum)
  - Call `flash_attn_varlen_func(q_packed, k_packed, v_packed, cu_seqlens, cu_seqlens, max_seqlen, max_seqlen)`
  - Assert output shape is `(total_tokens, num_heads, head_dim)` where `total_tokens = 896`
- `test_varlen_equivalence` — Compare padded attention and varlen attention give same results for the non-padded positions

### Expected Functionality

- At seq_len=2048 with fp16 on a modern GPU, FlashAttention forward pass is at least 2x faster than `F.scaled_dot_product_attention`
- Memory usage for FlashAttention at seq_len=4096 is at most 40% of standard attention memory
- Correctness tests pass with `atol=1e-3` for fp16 comparisons
- Benchmarks print formatted tables and skip OOM configurations gracefully

## Acceptance Criteria

- Benchmark utilities correctly measure time with CUDA events and include warmup iterations
- TFLOPS formula uses correct FLOPs count (halved for causal)
- Correctness tests cast to float32 before comparison to avoid dtype-specific comparison issues
- All tests skip gracefully on CPU-only environments and when `flash_attn` is not installed
- Shape tests cover all required head dimensions (32, 64, 128, 256)
- Variable-length test correctly computes `cu_seqlens` as cumulative sum
- `pip install -e . && python -c 'import flash_attn'` succeeds
- `python -m pytest /workspace/tests/test_v3_performance_optimization.py -v --tb=short` passes
