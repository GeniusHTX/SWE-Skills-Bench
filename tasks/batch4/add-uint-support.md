# Task: Add Unsigned Integer Support to PyTorch Reduction Operators

## Background

The PyTorch repository (https://github.com/pytorch/pytorch) is progressively expanding unsigned integer type coverage across its operator library. Several CUDA and CPU reduction operators (e.g., `min`, `max`, `sum`, `prod`) currently dispatch only over signed integral and floating-point types, leaving `uint16`, `uint32`, and `uint64` unsupported. These operators need to be updated so that tensors created with unsigned integer dtypes can flow through the standard reduction paths without runtime errors.

## Files to Create/Modify

- `aten/src/ATen/native/cuda/ReduceMinMaxKernel.cu` (modify) — Add unsigned integer type coverage to the min/max reduction CUDA kernels
- `aten/src/ATen/native/cuda/ReduceOpsKernel.cu` (modify) — Add unsigned integer type coverage to sum/prod CUDA reduction kernels
- `aten/src/ATen/native/cpu/ReduceOpsKernel.cpp` (modify) — Add unsigned integer type coverage to the corresponding CPU reduction dispatch sites
- `aten/src/ATen/native/ReduceOps.cpp` (modify) — Update any top-level dispatch wrappers that gate type support before delegating to backend kernels

## Requirements

### Dispatch Macro Updates

- All targeted reduction operator dispatch sites must accept `uint16`, `uint32`, and `uint64` dtypes in addition to their current type coverage
- Dispatch macros must use the V2 form (`AT_DISPATCH_V2`); any legacy `AT_DISPATCH_ALL_TYPES_AND*` call sites in the targeted files must be converted before adding unsigned types
- Type groups must be wrapped with `AT_EXPAND()` and appear as comma-separated arguments in the dispatch macro call
- Operators that only dispatch over floating-point types (e.g., `mean`) must **not** receive unsigned integer support

### Consistency Across Backends

- When a CUDA kernel gains unsigned integer support, the corresponding CPU kernel for the same operator must also be updated
- Every dispatch site within a single operator implementation file must be updated — partial coverage within a file is not acceptable

### Correctness Constraints

- `torch.min(uint32_tensor)` and `torch.max(uint64_tensor)` must return correct scalar values without overflow or sign-extension errors
- `torch.sum(uint16_tensor)` must accumulate without wrapping to a signed type
- Operators must continue to function correctly for all previously supported types after the change

### Expected Functionality

- A `torch.ones(4, dtype=torch.uint32).sum()` call returns a tensor with value `4` and dtype `uint32`
- `torch.tensor([3, 1, 4, 1, 5], dtype=torch.uint64).min()` returns `1`
- `torch.tensor([3, 1, 4, 1, 5], dtype=torch.uint16).max()` returns `5`
- Dispatching a float-only operator (e.g., `mean`) on a uint32 tensor raises the existing "not implemented" error rather than silently producing garbage
- All existing reduction operator tests continue to pass after the changes

## Acceptance Criteria

- PyTorch builds successfully with the modified files (`python setup.py develop` completes without errors)
- Reduction operators (`min`, `max`, `sum`, `prod`) accept uint16, uint32, and uint64 tensors and return correct results on both CPU and CUDA backends
- All dispatch macros in the modified files use the V2 form with properly wrapped type groups
- Float-only operators remain unchanged and continue to reject unsigned integer inputs
- No regressions in existing operator behavior for previously supported dtypes
