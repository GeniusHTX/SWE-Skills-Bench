# Task: Implement a JavaScript Hash Class Using Bun's Zig-JSC Bindings

## Background

Bun (https://github.com/oven-sh/bun) uses a code generation system where `.classes.ts` definition files describe JavaScript class interfaces and corresponding `.zig` files implement the native logic through JavaScriptCore bindings. A new hash utility class is needed that exposes multiple hash algorithms to JavaScript, implemented in Zig with proper JSC interop.

## Files to Create

- `src/bun.js/api/BunHasher.classes.ts` — JavaScript class definition describing the API surface for the code generator
- `src/bun.js/api/BunHasher.zig` — Zig native implementation with hash logic and JSC binding methods
- `test/js/bun/hasher.test.ts` — JavaScript test file validating the class behavior

## Requirements

### Class Definition

- Define a class using Bun's code generator `define()` pattern
- Declare a constructor, prototype methods for hashing and digesting, and a property getter
- Enable resource cleanup via finalization

### Zig Implementation

- Implement a Zig struct with constructor, hash computation, digest output, and property getter
- Support multiple hash algorithm variants selectable at construction time
- Accept both string and binary (Uint8Array) inputs for hashing
- Implement proper memory management with cleanup in the finalizer
- Expose at least three public functions and integrate with at least three JSC interface methods

### Test Suite

- Test each supported hash algorithm
- Test various input types: empty strings, ASCII text, Unicode content, and binary data
- Verify deterministic output (same input produces same hash)

## Expected Functionality

- Constructing an instance with a valid algorithm name succeeds
- The hash method returns consistent values for identical inputs
- The property getter returns the configured algorithm name
- Invalid algorithm names produce a clear error

## Acceptance Criteria

- JavaScript code can construct the new hash class with a supported algorithm name and use it through the generated JSC bindings.
- The class accepts both string input and binary input and produces deterministic digest results for repeated runs.
- The exposed getter returns the configured algorithm and invalid algorithm names produce a clear error.
- Native resources are cleaned up correctly when instances are finalized.
- The Zig implementation and class definition align so the generated Bun binding surface is complete and usable from JavaScript.
