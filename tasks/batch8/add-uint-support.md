# Task: Add Unsigned Integer Type Support to PyTorch Operators

## Background

The PyTorch tensor library has partial support for unsigned integer types (`uint16`, `uint32`, `uint64`). Several core operators — including reduction, comparison, clamping, and bitwise ops — currently only dispatch over signed integer and floating-point scalar types via `AT_DISPATCH` macros. These operators need to be updated so that tensors with `dtype=torch.uint16`, `torch.uint32`, or `torch.uint64` can be used without hitting "not implemented for 'UInt32'" runtime errors.

## Files to Create/Modify

- `aten/src/ATen/native/ReduceOps.cpp` (modify) — CPU reduction kernels for `aten::min` and `aten::max`; update dispatch macros to include unsigned integer types
- `aten/src/ATen/native/cuda/ReduceMinMaxKernel.cu` (modify) — CUDA reduction kernels for `aten::min` / `aten::max`; update dispatch macros to include unsigned integer types
- `aten/src/ATen/native/TensorCompare.cpp` (modify) — CPU implementations of `aten::clamp`, `aten::clamp_min`, `aten::clamp_max`, and `aten::where`; update dispatch macros to include unsigned integer types
- `aten/src/ATen/native/cuda/TensorCompare.cu` (modify) — CUDA implementations of `aten::clamp`, `aten::clamp_min`, `aten::clamp_max`; update dispatch macros to include unsigned integer types
- `aten/src/ATen/native/cpu/BinaryOpsKernel.cpp` (modify) — CPU bitwise kernels for `aten::bitwise_and`, `aten::bitwise_or`, `aten::bitwise_xor`; update dispatch macros to include unsigned integer types
- `aten/src/ATen/native/cuda/BinaryBitwiseOpsKernels.cu` (modify) — CUDA bitwise kernels for `aten::bitwise_and`, `aten::bitwise_or`, `aten::bitwise_xor`; update dispatch macros to include unsigned integer types

## Requirements

### Reduction Operators (`aten::min`, `aten::max`)

- `torch.min(t)` and `torch.max(t)` must return the correct scalar value when `t` has dtype `torch.uint16`, `torch.uint32`, or `torch.uint64`
- `torch.min(t, dim=d)` and `torch.max(t, dim=d)` must return both the values tensor and the indices tensor with the correct results for unsigned integer inputs
- The CPU and CUDA code paths must both be updated; a uint64 tensor created on CPU and moved to CUDA must produce the same reduction result
- Large unsigned values (e.g., `2**32 - 1` for uint32, `2**64 - 1` for uint64) must not wrap or be misinterpreted as negative numbers during comparison

### Clamping Operators (`aten::clamp`, `aten::clamp_min`, `aten::clamp_max`)

- `torch.clamp(t, min=a, max=b)` must correctly clamp unsigned integer tensors to the given bounds
- `torch.clamp_min(t, 0)` on a uint32 tensor must be a no-op (values are already non-negative)
- `torch.clamp_max(t, 255)` on a uint16 tensor must clamp values exceeding 255 down to 255
- When both `min` and `max` scalars are provided, they must be properly applied without signed/unsigned comparison bugs

### Conditional Selection (`aten::where`)

- `torch.where(condition, x, y)` must work when `x` and `y` are unsigned integer tensors of the same dtype
- The condition tensor is a boolean tensor; the output tensor must preserve the unsigned dtype
- Mixed-dtype broadcasting between unsigned and signed integer tensors is not required — same-dtype unsigned inputs are sufficient

### Bitwise Operators (`aten::bitwise_and`, `aten::bitwise_or`, `aten::bitwise_xor`)

- `torch.bitwise_and(a, b)`, `torch.bitwise_or(a, b)`, `torch.bitwise_xor(a, b)` must operate correctly on uint16, uint32, and uint64 tensor pairs
- Bitwise operations on unsigned types must produce results consistent with the C++ unsigned integer semantics (no sign extension)
- Both CPU and CUDA kernels must be updated
- Scalar-tensor combinations (e.g., `torch.bitwise_and(uint32_tensor, 0xFF)`) must work

### General Constraints

- All changes must use the `AT_DISPATCH_V2` macro format; any operator still using the legacy `AT_DISPATCH_ALL_TYPES` macro must first be converted to V2 format before adding unsigned type coverage
- The unsigned type groups (`AT_BAREBONES_UNSIGNED_TYPES` or `AT_INTEGRAL_TYPES_V2`) defined in `aten/src/ATen/Dispatch.h` must be used — do not add `kUInt16`, `kUInt32`, `kUInt64` as individual scalar types in the dispatch list
- Existing behavior for all previously supported dtypes (float32, float64, int32, int64, int16, int8, uint8, bfloat16, float16, bool) must not regress

## Expected Functionality

- `torch.min(torch.tensor([3, 1, 2], dtype=torch.uint32))` returns `tensor(1, dtype=torch.uint32)`
- `torch.max(torch.tensor([0, 4294967295], dtype=torch.uint32))` returns `tensor(4294967295, dtype=torch.uint32)` (2^32 − 1)
- `torch.clamp(torch.tensor([0, 500, 1000], dtype=torch.uint16), min=100, max=800)` returns `tensor([100, 500, 800], dtype=torch.uint16)`
- `torch.where(torch.tensor([True, False, True]), torch.tensor([10, 20, 30], dtype=torch.uint64), torch.tensor([40, 50, 60], dtype=torch.uint64))` returns `tensor([10, 50, 30], dtype=torch.uint64)`
- `torch.bitwise_and(torch.tensor([0xFF00], dtype=torch.uint16), torch.tensor([0x0F0F], dtype=torch.uint16))` returns `tensor([0x0F00], dtype=torch.uint16)`
- All of the above work identically on both CPU and CUDA devices

## Acceptance Criteria

- `aten::min` and `aten::max` (both single-tensor and dim-reduction variants) execute without errors for uint16, uint32, and uint64 tensors on CPU and CUDA, returning numerically correct results including at boundary values (0, max representable value)
- `aten::clamp`, `aten::clamp_min`, and `aten::clamp_max` execute without errors for uint16, uint32, and uint64 tensors, clamping values correctly without signed/unsigned misinterpretation
- `aten::where` executes without errors for uint16, uint32, and uint64 tensors, preserving the unsigned dtype in the output
- `aten::bitwise_and`, `aten::bitwise_or`, and `aten::bitwise_xor` execute without errors for uint16, uint32, and uint64 tensors on CPU and CUDA, producing bit-exact results consistent with C++ unsigned integer semantics
- The project builds successfully with `MAX_JOBS=4 USE_CUDA=0 python setup.py develop`
- All preexisting operator tests for signed integer and floating-point types continue to pass without regression
