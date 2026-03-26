# Task: Add Sliding Window Attention Support to Flash Attention

## Background

Flash Attention (https://github.com/Dao-AILab/flash-attention) provides optimized GPU attention kernels. A new feature is needed to support sliding window attention, where each token only attends to a fixed-size window of preceding tokens rather than the full sequence. This reduces memory usage and computation for long sequences while maintaining local context.

## Files to Create/Modify

- `flash_attn/flash_attn_sliding_window.py` (create) — Sliding window attention Python interface
- `flash_attn/flash_attn_interface.py` (modify) — Extend public API with `window_size` parameter

## Requirements

### Sliding Window

- Implement a sliding window attention mechanism with a configurable window size
- Each token at position `i` attends only to tokens in positions `[max(0, i - window_size + 1), i]`
- Tokens outside the window receive an attention weight of zero (masked out)

### Interface

- Expose the sliding window option as a parameter (e.g., `window_size`) in the attention function
- When `window_size` is `None` or `-1`, fall back to standard full attention
- Accept the same input tensor shapes as the existing Flash Attention interface (query, key, value)

### Correctness

- The output must match a naive reference implementation of sliding window attention within numerical tolerance
- Support causal and non-causal modes
- Handle edge cases: window size larger than sequence length (equivalent to full attention), window size of 1 (self-only attention)

### Build

- The package must install successfully and the `flash_attn` module must be importable

## Expected Functionality

- Calling attention with a window size restricts each token's attention to its local window
- Memory usage scales with window size rather than full sequence length
- Full attention behavior is preserved when no window size is specified

## Acceptance Criteria

- The attention interface accepts a configurable sliding-window parameter and preserves the existing full-attention behavior when the parameter is disabled.
- Each token attends only to the configured local window in sliding-window mode.
- Outputs match a straightforward reference implementation within reasonable numerical tolerance.
- Edge cases such as window size `1`, window size larger than the sequence length, and causal versus non-causal operation are handled correctly.
- The feature integrates into the existing Flash Attention API rather than introducing a disconnected standalone path.
