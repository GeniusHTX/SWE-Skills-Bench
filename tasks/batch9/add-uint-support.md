# Task: Add uint32/uint64 Support to Reduction Operators

## Background

The PyTorch repository (https://github.com/pytorch/pytorch) has ongoing work to expand unsigned integer type support across its operator set. Several CUDA reduction kernels in `aten/src/ATen/native/cuda/` currently dispatch over signed integer and floating-point types but do not include the barebones unsigned types (`kUInt16`, `kUInt32`, `kUInt64`). These reduction operators — min-values, max-values, argmin, argmax, and cumulative sum — need their `AT_DISPATCH_V2` macro call sites updated so that tensors with dtypes `torch.uint16`, `torch.uint32`, and `torch.uint64` are accepted.

## Files to Create/Modify

- `aten/src/ATen/native/cuda/ReduceMinValuesKernel.cu` (modify) — Add unsigned integer type coverage to the min-values reduction dispatch sites
- `aten/src/ATen/native/cuda/ReduceMaxValuesKernel.cu` (modify) — Add unsigned integer type coverage to the max-values reduction dispatch sites
- `aten/src/ATen/native/cuda/ReduceArgMinKernel.cu` (modify) — Add unsigned integer type coverage to the argmin dispatch site
- `aten/src/ATen/native/cuda/ReduceArgMaxKernel.cu` (modify) — Add unsigned integer type coverage to the argmax dispatch site
- `aten/src/ATen/native/cuda/CumsumKernel.cu` (modify) — Add unsigned integer type coverage to the cumulative sum dispatch site

## Requirements

### Type Dispatch Updates

- Each file's `AT_DISPATCH_V2` macro call must be updated so that `kUInt16`, `kUInt32`, and `kUInt64` are included in the dispatched type set
- If a file still uses a legacy `AT_DISPATCH_ALL_TYPES_AND*` macro, it must first be converted to the `AT_DISPATCH_V2` form before unsigned types are added
- All dispatch sites within a single file must be updated consistently — if a file contains multiple kernel launch functions, every relevant dispatch macro in that file must gain unsigned type coverage
- Dispatch macros that cover only floating-point types (e.g., `AT_EXPAND(AT_FLOATING_TYPES)` alone) must not be modified, since unsigned integer types are not meaningful for those call sites

### Correctness Constraints

- The min/max reduction kernels must produce correct results for `uint32` and `uint64` tensors, including tensors that contain values above `INT32_MAX` or `INT64_MAX` respectively
- The argmin/argmax kernels must return correct indices for unsigned-typed input tensors
- The cumulative sum kernel must handle unsigned overflow according to C++ unsigned arithmetic rules (wrap-around, not undefined behavior)
- No existing dtype support may be removed or broken — all previously supported types must continue to work identically

### Edge Cases

- A single-element `uint64` tensor with value `2^64 - 1` must return that value as-is from `min` and `max`
- Argmin on a `uint32` tensor where all elements are equal must return index `0`
- Cumsum on a `uint64` tensor `[2^64 - 1, 1]` must wrap to `[2^64 - 1, 0]` without crashing

## Acceptance Criteria

- The project builds successfully with `MAX_JOBS=4 USE_CUDA=0 python setup.py develop`
- `torch.min`, `torch.max`, `torch.argmin`, `torch.argmax`, and `torch.cumsum` accept `torch.uint16`, `torch.uint32`, and `torch.uint64` tensors without raising a `RuntimeError` about unsupported dtype
- Reduction results on unsigned tensors are numerically correct, including values exceeding the signed range of the same width
- All previously passing tests in `test/test_reductions.py` continue to pass without modification
