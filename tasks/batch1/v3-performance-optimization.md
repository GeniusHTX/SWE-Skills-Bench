# Task: Add Flash Attention Performance Benchmark and Optimization Examples

## Background
   Create performance benchmarks and optimization examples for Flash Attention
   demonstrating speedup comparisons with standard attention mechanisms.

## Files to Create/Modify
   - benchmarks/benchmark_attention.py (new)
   - benchmarks/configs/benchmark_config.yaml (new)
   - examples/optimization_demo.py (new)

## Requirements
   
   Benchmark Script (benchmark_attention.py):
   - Compare Flash Attention vs standard PyTorch attention
   - Test multiple sequence lengths: 512, 1024, 2048, 4096
   - Test multiple head dimensions: 64, 128
   - Measure forward and backward pass separately
   - Output speedup ratios (target: 2.49x-7.47x)
   - Memory usage comparison
   
   Configuration (benchmark_config.yaml):
   - batch_sizes: [1, 4, 8, 16]
   - seq_lengths: [512, 1024, 2048, 4096]
   - head_dim: [64, 128]
   - num_heads: [8, 12, 16]
   - dtype: [float16, bfloat16]
   
   Optimization Demo (optimization_demo.py):
   - Demonstrate causal masking optimization
   - Show memory-efficient backward pass
   - Include dropout optimization example
   - Performance timing decorators

4. Output Requirements:
   - JSON results file with speedup metrics
   - Memory reduction percentages
   - Latency comparisons (ms)

## Acceptance Criteria
   - `python benchmarks/benchmark_attention.py` exits with code 0
   - Benchmark results show Flash Attention speedup > 2x
   - Memory reduction > 40% for long sequences
