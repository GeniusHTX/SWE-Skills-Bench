# Task: Add Unsigned Integer Support to PyTorch Bitwise and Comparison Operators

## Background

The PyTorch repository (https://github.com/pytorch/pytorch) has introduced barebones unsigned integer types (`uint16`, `uint32`, `uint64`) but many operators still lack support for these types in their `AT_DISPATCH` macros. Several bitwise and comparison operators need to be updated so that tensors with unsigned integer dtypes can pass through these operations without runtime dispatch errors.

## Files to Create/Modify

- `aten/src/ATen/native/cpu/BinaryOpsKernel.cpp` (modify) — Add unsigned integer dispatch support to the bitwise binary operator kernels (`bitwise_and`, `bitwise_or`, `bitwise_xor`)
- `aten/src/ATen/native/cpu/UnaryOpsKernel.cpp` (modify) — Add unsigned integer dispatch support to the `bitwise_not` unary operator kernel
- `aten/src/ATen/native/cuda/BinaryBitwiseOpsKernels.cu` (modify) — Add unsigned integer dispatch to CUDA bitwise binary operator kernels (`bitwise_and`, `bitwise_or`, `bitwise_xor`)
- `aten/src/ATen/native/cuda/UnaryBitwiseOpsKernels.cu` (modify) — Add unsigned integer dispatch to CUDA `bitwise_not` kernel
- `aten/src/ATen/native/cpu/CompareKernel.cpp` (modify) — Add unsigned integer dispatch support to comparison operator kernels (`eq`, `ne`, `lt`, `le`, `gt`, `ge`)

## Requirements

### Bitwise Operators — CPU

- The `bitwise_and`, `bitwise_or`, and `bitwise_xor` kernels in the CPU binary ops file must dispatch over `kUInt16`, `kUInt32`, and `kUInt64` in addition to the currently supported types.
- The `bitwise_not` kernel in the CPU unary ops file must dispatch over `kUInt16`, `kUInt32`, and `kUInt64`.
- The dispatch macros must use the `AT_DISPATCH_V2` format. If a kernel still uses the legacy `AT_DISPATCH_ALL_TYPES*` macro, it must first be converted to `AT_DISPATCH_V2` before adding unsigned type coverage.

### Bitwise Operators — CUDA

- The same bitwise operators (`bitwise_and`, `bitwise_or`, `bitwise_xor`, `bitwise_not`) must also gain unsigned integer dispatch in their CUDA kernel files.
- The CUDA kernels must handle `kUInt16`, `kUInt32`, and `kUInt64` correctly, and ensure the scalar type instantiation compiles for these unsigned widths.

### Comparison Operators — CPU

- The six standard comparison kernels (`eq`, `ne`, `lt`, `le`, `gt`, `ge`) in the CPU compare kernel file must dispatch over `kUInt16`, `kUInt32`, and `kUInt64`.
- Unsigned comparison semantics must be preserved — for example, `torch.tensor([0], dtype=torch.uint32) > torch.tensor([4294967295], dtype=torch.uint32)` must return `False`.

### Expected Functionality

- `torch.bitwise_and(a, b)` where `a` and `b` are `torch.uint32` tensors → returns a `torch.uint32` tensor with the correct per-element AND result.
- `torch.bitwise_not(a)` where `a` is a `torch.uint64` tensor containing `0` → returns a tensor containing `18446744073709551615` (all bits set).
- `torch.eq(a, b)` where both are `torch.uint16` tensors with identical values → returns an all-`True` boolean tensor.
- `torch.lt(torch.tensor([0], dtype=torch.uint32), torch.tensor([1], dtype=torch.uint32))` → returns `tensor([True])`.
- Passing a `torch.uint32` tensor to `bitwise_xor` on CUDA → executes without a dispatch error and returns the correct result.
- Attempting `torch.bitwise_and` between a `uint32` tensor and a `float32` tensor → raises a dtype promotion error (unsigned bitwise ops are integer-only).

## Acceptance Criteria

- All six bitwise and comparison operators (`bitwise_and`, `bitwise_or`, `bitwise_xor`, `bitwise_not`, `eq`, `ne`, `lt`, `le`, `gt`, `ge`) accept `torch.uint16`, `torch.uint32`, and `torch.uint64` tensors on CPU without raising a dispatch error.
- The four bitwise operators also accept `torch.uint32` and `torch.uint64` tensors on CUDA without raising a dispatch error.
- Bitwise operations on unsigned tensors produce numerically correct results consistent with C++ unsigned arithmetic.
- Comparison operations on unsigned tensors produce correct boolean results respecting unsigned ordering.
- All dispatch macros in the modified files use the `AT_DISPATCH_V2` format.
- The project builds successfully with `MAX_JOBS=4 USE_CUDA=0 python setup.py develop`.
