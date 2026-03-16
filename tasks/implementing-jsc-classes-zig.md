# Task: Implement BunHash JavaScript Class Using Zig Bindings

## Background

Implement a new `BunHash` JavaScript class in Bun's runtime that exposes multiple hash algorithms (murmur3, xxhash32, xxhash64, wyhash) to JavaScript. The class should be implemented using Bun's `.classes.ts` definition file and Zig implementation pattern.

## Files to Create/Modify

- `src/bun.js/api/BunHash.classes.ts` - Class definition file for the code generator
- `src/bun.js/api/BunHash.zig` - Zig implementation of the hash class
- `test/js/bun/hash/hash.test.ts` - Comprehensive test suite

## Requirements

### Class Definition (BunHash.classes.ts)
Define the class using Bun's `define()` pattern:
- `name: "BunHash"`
- `constructor: true`
- Prototype methods: `hash(data)`, `digest()`
- Prototype getters: `algorithm` (cached)
- `finalize: true` for cleanup

### Zig Implementation (BunHash.zig)
- Implement `constructor` accepting algorithm name string
- Supported algorithms: `"murmur3"`, `"xxhash32"`, `"xxhash64"`, `"wyhash"`
- `hash(data)` method: Accept string or Uint8Array, return hash value
- `digest()` method: Return hex string of current hash
- `getAlgorithm` getter: Return algorithm name
- Proper `deinit` and `finalize` for memory cleanup

### Test Suite (hash.test.ts)
- Test all 4 hash algorithms
- Test scenarios: empty string, ASCII, Unicode/UTF-8, binary data (Uint8Array)
- Known test vector verification
- Large input (>1MB) handling

## Acceptance Criteria

- `bun run build` compiles without errors
- `BunHash` class is accessible from JavaScript
- All hash algorithms produce correct, consistent results
- Test suite covers all algorithms and edge cases
