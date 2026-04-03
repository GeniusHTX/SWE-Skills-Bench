# Task: Add Unsigned Integer Type Support to PyTorch CUDA Reduction and Sorting Operators

## Background

The PyTorch repository (https://github.com/pytorch/pytorch) supports unsigned integer types (`uint16`, `uint32`, `uint64`) at the dtype level, but many existing CUDA kernel operators do not yet dispatch over these types. Several reduction and sorting operators in `aten/src/ATen/native/cuda/` currently only support signed integral and floating-point types, causing runtime errors when users pass `torch.uint32` or `torch.uint64` tensors to these operations.

## Files to Create/Modify

- `aten/src/ATen/native/cuda/ReduceMinMaxKernel.cu` (modify) — Add uint16/uint32/uint64 dispatch support to min and max reduction kernels
- `aten/src/ATen/native/cuda/SortingKernel.cu` (modify) — Add uint16/uint32/uint64 dispatch support to sort and argsort kernels
- `aten/src/ATen/native/cuda/CumsumKernel.cu` (modify) — Add uint16/uint32/uint64 dispatch support to cumulative sum kernels
- `aten/src/ATen/native/cuda/CompareKernels.cu` (modify) — Add uint16/uint32/uint64 dispatch support to element-wise comparison kernels (eq, ne, lt, le, gt, ge)

## Requirements

### Type Coverage

- Each of the four target files must accept tensors of dtype `torch.uint16`, `torch.uint32`, and `torch.uint64` after modification
- The `kUInt16`, `kUInt32`, and `kUInt64` scalar types must be included in every type-dispatch site within each file
- Existing type support (signed integers, floating point, `kHalf`, `kBFloat16`, `kBool`) must remain unchanged

### Operator-Specific Behavior

#### ReduceMinMaxKernel.cu
- `min_values` and `max_values` must accept uint16/uint32/uint64 input tensors and produce correct minimum/maximum results
- `min` and `max` (with indices) must return both the correct value and the correct index for unsigned integer inputs
- Results for unsigned types must respect unsigned comparison semantics (e.g., 0 < 65535 for uint16)

#### SortingKernel.cu
- `sort` must correctly order uint32 and uint64 tensors in both ascending and descending modes
- `argsort` must return correct index permutations for unsigned integer inputs
- Sorting must handle the full unsigned range without overflow (e.g., values up to 2^64 − 1 for uint64)

#### CumsumKernel.cu
- `cumsum` must produce correct prefix sums for uint16/uint32/uint64 tensors
- Unsigned overflow behavior must follow standard C++ unsigned arithmetic (wrap-around, not UB)

#### CompareKernels.cu
- All six comparison operators (`eq`, `ne`, `lt`, `le`, `gt`, `ge`) must support uint16/uint32/uint64 operands
- Mixed-type comparisons between unsigned types and other numeric types must follow PyTorch's existing type promotion rules

### Consistency

- Every dispatch site within each modified file must be updated, not just the first occurrence
- If a file contains multiple kernel launch functions (e.g., a `_kernel` launcher and a `_launch` helper), all dispatch sites must include the unsigned types
- The changes must not alter the dispatch format or structure of existing macros beyond what is necessary to add the new types

## Expected Functionality

- `torch.min(torch.tensor([3, 1, 2], dtype=torch.uint32))` → returns `tensor(1, dtype=torch.uint32)` instead of raising a RuntimeError
- `torch.sort(torch.tensor([300, 100, 200], dtype=torch.uint64))` → returns `(tensor([100, 200, 300], dtype=torch.uint64), tensor([1, 2, 0]))`
- `torch.cumsum(torch.tensor([1, 2, 3], dtype=torch.uint32), dim=0)` → returns `tensor([1, 3, 6], dtype=torch.uint32)`
- `torch.eq(torch.tensor([1, 2], dtype=torch.uint16), torch.tensor([1, 3], dtype=torch.uint16))` → returns `tensor([True, False])`
- Existing signed-integer and floating-point behavior for all four operators is unchanged
- The project builds successfully with `USE_CUDA=0 python setup.py develop`

## Acceptance Criteria

- All four target files include uint16, uint32, and uint64 in their type dispatch, covering every dispatch site in each file
- `torch.min`, `torch.max`, `torch.sort`, `torch.cumsum`, and the six comparison operators accept uint32 and uint64 tensors without RuntimeError
- Unsigned integer results are numerically correct under unsigned comparison and arithmetic semantics
- No regressions for previously supported dtypes (signed integers, floats, half, bfloat16, bool)
- The PyTorch build completes without errors
