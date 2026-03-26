# Task: Restore Uint32 and Uint64 Operator Dispatch Support in PyTorch

## Background

PyTorch (https://github.com/pytorch/pytorch) is a deep learning framework. Recent changes broke operator support for unsigned integer types (`uint32` and `uint64`). The `AT_DISPATCH_ALL_TYPES` and related dispatch macros in `aten/src/ATen/Dispatch.h` do not include uint32/uint64, causing runtime errors when tensor operations are attempted on these dtypes. The dispatch macros and affected operators need to be extended to handle unsigned integer types.

## Files to Create/Modify

- `aten/src/ATen/Dispatch.h` (modify) — Extend `AT_DISPATCH_ALL_TYPES_AND` macros to support uint32 and uint64 dtypes
- `aten/src/ATen/native/UnaryOps.cpp` (modify) — Add uint32/uint64 dispatch to unary operations (abs, neg, bitwise_not)
- `aten/src/ATen/native/BinaryOps.cpp` (modify) — Add uint32/uint64 dispatch to binary operations (add, sub, mul, div, bitwise_and, bitwise_or, bitwise_xor)
- `aten/src/ATen/native/CompareOps.cpp` (modify) — Add uint32/uint64 dispatch to comparison operations (eq, ne, lt, le, gt, ge)
- `test/test_uint_ops.py` (create) — Tests verifying uint32 and uint64 operators work correctly

## Requirements

### Dispatch Macro Extension

- Add a new macro `AT_DISPATCH_ALL_TYPES_AND_UINT` that includes `kUInt32` and `kUInt64` in addition to all existing types
- Wrap the new macro entries with `AT_EXPAND` as required by PyTorch's dispatch system for proper template instantiation
- Ensure the macro works with both CPU and CUDA dispatchers
- The existing `AT_DISPATCH_ALL_TYPES` macro must remain unchanged for backward compatibility

### Unary Operations

- Extend the following unary operations to dispatch on uint32 and uint64:
  - `bitwise_not` — flip all bits; result is the same uint type
  - `abs` — identity operation for unsigned types (unsigned numbers are always non-negative)
  - Negative (`neg`) on unsigned types should raise a runtime error with message indicating that negation is not supported for unsigned integer types

### Binary Operations

- Extend the following binary operations to dispatch on uint32 and uint64:
  - Arithmetic: `add`, `sub`, `mul`, `div` (integer division for uint types)
  - Bitwise: `bitwise_and`, `bitwise_or`, `bitwise_xor`
- `sub` on unsigned types where the result would underflow (B > A in A - B) should wrap around (standard unsigned integer behavior, matching C++ semantics)
- `div` by zero on unsigned types should raise a runtime error

### Comparison Operations

- Extend `eq`, `ne`, `lt`, `le`, `gt`, `ge` to dispatch on uint32 and uint64
- Comparison results should be `bool` tensors (same as existing integer comparison behavior)

### Expected Functionality

- `torch.tensor([1, 2, 3], dtype=torch.uint32) + torch.tensor([4, 5, 6], dtype=torch.uint32)` returns `tensor([5, 7, 9], dtype=torch.uint32)`
- `torch.tensor([255], dtype=torch.uint32).bitwise_not()` returns correct bitwise complement
- `torch.tensor([1, 2, 3], dtype=torch.uint64) > torch.tensor([2, 2, 2], dtype=torch.uint64)` returns `tensor([False, False, True])`
- `torch.tensor([1], dtype=torch.uint32) - torch.tensor([2], dtype=torch.uint32)` wraps around (unsigned underflow)
- `-torch.tensor([1], dtype=torch.uint32)` raises RuntimeError about negation not supported for unsigned types
- `torch.div(torch.tensor([10], dtype=torch.uint32), torch.tensor([0], dtype=torch.uint32))` raises RuntimeError about division by zero

## Acceptance Criteria

- `AT_DISPATCH_ALL_TYPES_AND_UINT` macro exists and includes `kUInt32` and `kUInt64`
- Existing `AT_DISPATCH_ALL_TYPES` macro is unchanged (backward compatible)
- Unary operations (`bitwise_not`, `abs`) work on uint32 and uint64 tensors
- `neg` on unsigned types raises RuntimeError with descriptive message
- Binary arithmetic and bitwise operations work on uint32 and uint64 tensors
- Unsigned subtraction underflow wraps around per C++ unsigned semantics
- Division by zero on unsigned types raises RuntimeError
- Comparison operations return bool tensors for uint32 and uint64 inputs
- `MAX_JOBS=4 USE_CUDA=0 python setup.py develop` builds successfully
- Tests verify all operations for both uint32 and uint64 dtypes
