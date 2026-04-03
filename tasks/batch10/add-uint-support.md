# Task: Add uint16/uint32/uint64 Support to PyTorch Reduction Operators

## Background

PyTorch's reduction operators (min, max, sum, prod) in `aten/src/ATen/native/` currently dispatch over signed integer and floating-point types but do not cover the unsigned integer dtypes `kUInt16`, `kUInt32`, and `kUInt64`. These dtypes need to be added to the type-dispatch macros of several CUDA and CPU reduction kernels so that tensors created with `torch.uint16`, `torch.uint32`, and `torch.uint64` can flow through reduction operations without raising a dtype dispatch error.

## Files to Create/Modify

- `aten/src/ATen/native/cuda/ReduceMinValuesKernel.cu` (modify) — Add unsigned integer dtype coverage to the min-values CUDA kernel dispatch
- `aten/src/ATen/native/cuda/ReduceMaxValuesKernel.cu` (modify) — Add unsigned integer dtype coverage to the max-values CUDA kernel dispatch
- `aten/src/ATen/native/cuda/ReduceAMinMaxKernel.cu` (modify) — Add unsigned integer dtype coverage to the aminmax CUDA kernel dispatch
- `aten/src/ATen/native/SharedReduceOps.h` (modify) — Ensure reduction helper templates compile for `uint16_t`, `uint32_t`, `uint64_t`
- `aten/src/ATen/native/ReduceOps.cpp` (modify) — Add unsigned integer dtype coverage to the CPU reduction dispatch sites
- `test/test_reductions.py` (modify) — Add `torch.uint16`, `torch.uint32`, `torch.uint64` to the dtype parametrization for reduction tests

## Requirements

### Dispatch Macro Updates

- Every `AT_DISPATCH_V2` call site in the listed kernel files must include `kUInt16`, `kUInt32`, and `kUInt64` in its dispatched type set
- If a dispatch site currently uses `AT_EXPAND(AT_INTEGRAL_TYPES)` as a standalone group, replace it with `AT_EXPAND(AT_INTEGRAL_TYPES_V2)` which is the superset including barebones unsigned types
- If a dispatch site uses `AT_EXPAND(AT_ALL_TYPES)` (which decomposes into `AT_INTEGRAL_TYPES + AT_FLOATING_TYPES`), add `AT_EXPAND(AT_BAREBONES_UNSIGNED_TYPES)` as an additional type group argument
- Do not add unsigned types to dispatch sites that only cover floating-point types (e.g., `AT_EXPAND(AT_FLOATING_TYPES)` alone)
- Dispatch sites that already include `AT_EXPAND(AT_BAREBONES_UNSIGNED_TYPES)` or `AT_EXPAND(AT_INTEGRAL_TYPES_V2)` must not be modified

### Legacy Macro Conversion

- If any target file still uses legacy `AT_DISPATCH_ALL_TYPES`, `AT_DISPATCH_ALL_TYPES_AND`, or `AT_DISPATCH_ALL_TYPES_AND2` macros, convert them to `AT_DISPATCH_V2` before adding unsigned type coverage
- The converted macro must preserve the original type coverage (all previously dispatched types and extra scalar types such as `kHalf`, `kBFloat16`, `kBool`)
- The lambda body must be wrapped in `AT_WRAP(...)` when converting to `AT_DISPATCH_V2`

### Template Compatibility

- `aten/src/ATen/native/SharedReduceOps.h` must compile when instantiated with `uint16_t`, `uint32_t`, and `uint64_t` — verify that comparison operators and accumulator types are compatible
- Any `std::numeric_limits` usage in the reduction identity values must resolve correctly for the three unsigned types

### Consistency Across Dispatch Sites

- A single kernel file may contain multiple dispatch macros (e.g., one for the values kernel and one for the launch wrapper). All dispatch sites within the same file must receive the same unsigned type additions
- CPU and CUDA variants of the same logical operator must have matching unsigned type coverage

### Expected Functionality

- `torch.tensor([3, 1, 2], dtype=torch.uint16).min()` → returns `tensor(1, dtype=torch.uint16)`
- `torch.tensor([3, 1, 2], dtype=torch.uint32).max()` → returns `tensor(3, dtype=torch.uint32)`
- `torch.tensor([10, 20, 30], dtype=torch.uint64).sum()` → returns `tensor(60, dtype=torch.uint64)`
- `torch.aminmax(torch.tensor([5, 2, 8], dtype=torch.uint32))` → returns `(tensor(2, dtype=torch.uint32), tensor(8, dtype=torch.uint32))`
- Passing a `torch.float32` tensor to the same operators still works (no regression)
- Passing a dtype not covered by any dispatch group raises `RuntimeError` with an "unsupported dtype" message

## Acceptance Criteria

- `cd pytorch && MAX_JOBS=4 USE_CUDA=0 python setup.py develop` completes without compilation errors
- `torch.tensor([1,2,3], dtype=torch.uint16).min()` executes without a dispatch error on CPU
- `torch.tensor([1,2,3], dtype=torch.uint32).max()` executes without a dispatch error on CPU
- `torch.tensor([1,2,3], dtype=torch.uint64).sum()` executes without a dispatch error on CPU
- All previously passing reduction tests in `test/test_reductions.py` continue to pass
- No dispatch sites that exclusively cover floating-point types are modified
- Every modified dispatch site uses `AT_DISPATCH_V2` (no legacy macro forms remain in the modified files)
