# Task: Extend Unsigned Integer Type Coverage in PyTorch Operators

## Background

The PyTorch codebase (https://github.com/pytorch/pytorch) has partial support for unsigned integer types across its operator library. Several arithmetic and mathematical operators currently lack support for `uint16`, `uint32`, and `uint64` tensor types. When users pass tensors of these dtypes to unsupported operators, the runtime raises a dispatch error. The type dispatch infrastructure needs to be extended so that additional operators can accept unsigned integer inputs.

## Files to Modify

- `aten/src/ATen/native/BinaryOps.cpp` — Dispatch registration for arithmetic ops (add, sub, mul, floor_divide, remainder) and bitwise ops (and, or, xor, lshift, rshift)
- `aten/src/ATen/native/cpu/BinaryOpsKernel.cpp` — CPU kernel implementations for binary operators
- `aten/src/ATen/native/TensorCompare.cpp` — Dispatch registration for comparison ops (eq, ne, lt, le, gt, ge)
- `aten/src/ATen/native/GcdLcm.cpp` — GCD operator dispatch and implementation

## Requirements

1. Operators to support

- The implementation MUST explicitly add `uint16`, `uint32`, and `uint64` support for the following operators (operator names correspond to native ATen symbols and Python API where applicable):
	- Arithmetic: `add` (aten::add), `sub` (aten::sub), `mul` (aten::mul)
	- Integer division / remainder: `floor_divide` (aten::floor_divide), `remainder` (aten::remainder)
	- Bitwise and shifts: `bitwise_and` (aten::bitwise_and), `bitwise_or` (aten::bitwise_or), `bitwise_xor` (aten::bitwise_xor), `lshift`/`left_shift` (aten::lshift), `rshift`/`right_shift` (aten::rshift)
	- GCD: `gcd` (aten::gcd) when present in the codebase
	- Comparisons: `eq`, `ne`, `lt`, `le`, `gt`, `ge` (aten::* comparison ops)

2. Scope of changes

- For each operator above, update both the operator registration/type-dispatch tables and the CPU kernel implementations under `aten/src/ATen/native/` so that the operator accepts unsigned integer tensors without raising dispatch errors.
- If a kernel implementation is missing for an unsigned dtype, add an explicit kernel path (reuse signed-integer implementation where semantics match, or add a thin adapter that performs identical, dtype-preserving logic).
- Do NOT change operators that are inherently floating-point-only (e.g., `sqrt`, `sin`, `exp`).

3. Semantics and dtype rules

- When all inputs are the same unsigned integer dtype, the operator should preserve that dtype for outputs where that is semantically correct (e.g., `add(uint32, uint32) -> uint32`).
- For mixed-type inputs, follow existing PyTorch promotion rules; do not introduce new promotion behavior beyond existing signed-integer promotion rules.
- Integer division behavior: implement `floor_divide` and `remainder` semantics consistent with current PyTorch integer ops (no conversion to floating point), and ensure results for unsigned inputs match the mathematical remainder/quotient for non-negative integers.

4. Compatibility and robustness

- Ensure changes compile and pass existing unit tests unrelated to unsigned support.
- Provide fallbacks or clear error messages for operator combinations that remain unsupported (e.g., mixing unsigned with types that cannot be sensibly combined).

5. Implementation notes for contributors

- Prefer adding dtype coverage via dispatch table entries and small adapters rather than rewriting algorithmic kernels.
- Include small unit tests for each operator (see Acceptance Criteria) to validate behavior on sample inputs.

## Expected Functionality

- Operators that previously raised dispatch errors for `uint32` or `uint64` tensors now execute successfully and return correct results
- The output tensor dtype matches the input tensor dtype when all inputs share the same unsigned type
- Operators that only make sense for floating-point types remain unchanged

Additionally, the repository should include minimal unit tests that demonstrate correct behavior for each operator listed in the Requirements (examples in Acceptance Criteria). These tests should validate dtype preservation, numerical correctness for representative values, and reasonable behavior for edge cases (e.g., zero, max-value, boundary shifts).

## Acceptance Criteria

- The listed operators accept `uint16`, `uint32`, and `uint64` inputs without raising dispatch errors.
- Arithmetic, division, remainder, bitwise, GCD, and comparison results are numerically correct for representative unsigned inputs.
- When all inputs share the same unsigned dtype, the result keeps that dtype wherever PyTorch's existing promotion rules do not require otherwise.
- Edge cases including zero values, maximum representable values, and boundary shift counts behave consistently and do not crash.
- Floating-point-only operators remain unchanged and unsigned support is limited to operators with well-defined integer semantics.
