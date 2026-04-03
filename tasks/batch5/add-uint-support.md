# Task: Add uint32 and uint64 Support to Six CUDA Operators

## Background

PyTorch recently introduced unsigned integer scalar types (`uint16`, `uint32`, `uint64`), but many existing CUDA kernels still dispatch only over the signed integral types (`int8`, `int16`, `int32`, `int64`) plus `bool`. As a result, calling operators such as `torch.bitwise_and` or `torch.maximum` on `torch.uint32` / `torch.uint64` tensors raises a runtime dtype error on CUDA, even though the operations are mathematically well-defined for unsigned integers.

## Files to Create/Modify

- `aten/src/ATen/native/cuda/BinaryBitwiseOpsKernels.cu` (modify) — Extend the dispatch macros in `bitwise_and_kernel_cuda`, `bitwise_or_kernel_cuda`, and `bitwise_xor_kernel_cuda` to cover `uint32` and `uint64`.
- `aten/src/ATen/native/cuda/BinaryShiftOpsKernels.cu` (modify) — Extend the dispatch macros in `lshift_kernel_cuda` and `rshift_kernel_cuda` to cover `uint32` and `uint64`.
- `aten/src/ATen/native/cuda/MaxMinElementwiseKernel.cu` (modify) — Extend the integral dispatch path in `maximum_kernel_cuda` and `minimum_kernel_cuda` to cover `uint32` and `uint64`.

## Requirements

### Bitwise Operators (`bitwise_and`, `bitwise_or`, `bitwise_xor`)

- All three CUDA kernels currently use `AT_DISPATCH_INTEGRAL_TYPES_AND(kBool, ...)` which covers `int8`–`int64` and `bool` only.
- After modification, calling `torch.bitwise_and(a, b)` where `a` and `b` are `torch.uint32` tensors on CUDA must produce the correct element-wise result without error.
- The same applies for `bitwise_or` and `bitwise_xor`.
- The `bool` specialization must remain unchanged.

### Shift Operators (`__lshift__`, `__rshift__`)

- `lshift_kernel_cuda` and `rshift_kernel_cuda` currently use `AT_DISPATCH_INTEGRAL_TYPES(...)`.
- After modification, `torch.tensor([0xFFFFFFFF], dtype=torch.uint32, device='cuda') << 1` must return `0xFFFFFFFE` (not raise a dtype error).
- Right-shift on unsigned types must be a logical shift (zero-fill), not an arithmetic shift.
- Shift amount boundary behavior (shift ≥ bit-width) must produce 0 for left-shift and 0 for right-shift on unsigned types.

### Elementwise Min / Max (`maximum`, `minimum`)

- `maximum_kernel_cuda` and `minimum_kernel_cuda` dispatch integral types via `AT_DISPATCH_INTEGRAL_TYPES(...)`.
- After modification, `torch.maximum(a, b)` must work when `a` and `b` are `uint32` or `uint64` tensors on CUDA.
- The result dtype must remain `uint32` or `uint64` respectively (no implicit promotion to a signed type).

### Expected Functionality

- `torch.bitwise_and(torch.tensor([0xFF00FF00], dtype=torch.uint32, device='cuda'), torch.tensor([0x0F0F0F0F], dtype=torch.uint32, device='cuda'))` → tensor with value `0x0F000F00`, dtype `torch.uint32`.
- `torch.tensor([1], dtype=torch.uint64, device='cuda') << 63` → tensor with value `2**63`, dtype `torch.uint64`.
- `torch.tensor([2**64 - 1], dtype=torch.uint64, device='cuda') >> 32` → tensor with value `2**32 - 1`.
- `torch.maximum(torch.tensor([3000000000], dtype=torch.uint32, device='cuda'), torch.tensor([2000000000], dtype=torch.uint32, device='cuda'))` → tensor `[3000000000]`, dtype `torch.uint32`.
- Mixed `uint32` / `uint64` operations should follow PyTorch's standard type promotion rules.

## Acceptance Criteria

- `torch.bitwise_and`, `torch.bitwise_or`, and `torch.bitwise_xor` accept `uint32` and `uint64` tensor inputs on CUDA and return correct results.
- `torch.Tensor.__lshift__` and `torch.Tensor.__rshift__` accept `uint32` and `uint64` tensor inputs on CUDA; right-shift is logical (zero-fill) for unsigned types.
- `torch.maximum` and `torch.minimum` accept `uint32` and `uint64` tensor inputs on CUDA and preserve the unsigned dtype in the output.
- All six CUDA kernel files still compile successfully with `USE_CUDA=1`.
- Existing behavior for signed integer types (`int8`–`int64`) and `bool` is not altered.
