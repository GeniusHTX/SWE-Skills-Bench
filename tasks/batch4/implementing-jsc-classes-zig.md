# Task: Implement a URL Pattern Matcher Class for Bun Using Zig-JS Bindings

## Background

The Bun runtime (https://github.com/oven-sh/bun) uses a code generation system to bridge Zig implementations with JavaScript APIs via `.classes.ts` definitions. A new `URLPatternMatcher` class is needed that provides efficient URL pattern matching capabilities (similar to the URLPattern API) implemented in Zig for performance, exposed to JavaScript through Bun's bindings generator. The class must handle path parameter extraction, wildcard matching, and pattern compilation.

## Files to Create/Modify

- `src/bun.js/api/URLPatternMatcher.classes.ts` (create) — JavaScript interface definition for the class and its methods
- `src/bun.js/api/URLPatternMatcher.zig` (create) — Zig implementation of the pattern matching logic
- `src/bun.js/bindings/generated_classes_list.zig` (modify) — Register the new class in the generated classes list

## Requirements

### Class Definition (`.classes.ts`)

- Class name: `URLPatternMatcher`
- Must have a public constructor that accepts a pattern string
- Must set `finalize: true` for garbage collection cleanup
- Prototype methods:
  - `match` (1 argument) — tests a URL path against the compiled pattern, returns a match result object or `null`
  - `test` (1 argument) — returns a boolean indicating whether the path matches
- Prototype properties:
  - `pattern` (getter, cached) — returns the original pattern string
  - `paramNames` (getter, cached) — returns an array of parameter names extracted from the pattern

### Zig Implementation

- The constructor must parse and compile the pattern string into an internal representation that supports:
  - Static segments: `/users/list` matches only `/users/list`
  - Named parameters: `/users/:id` matches `/users/123` and captures `id=123`
  - Wildcard segments: `/files/*path` matches `/files/a/b/c` and captures the remainder as `path`
  - Optional trailing slash: `/users/:id` matches both `/users/123` and `/users/123/`
- `match(path)` must return a JavaScript object with `{ matched: true, params: { key: value } }` on success, or `null` on failure
- `test(path)` must return `true` or `false` without allocating a params object
- The constructor must throw a JavaScript error (using `globalObject.throw`) if the pattern is empty, contains consecutive slashes (`//`), or has an unnamed parameter (`:` followed by non-alphanumeric)
- Memory for the compiled pattern segments must be allocated with `bun.default_allocator` and freed in `deinit`

### Memory Management

- `deinit()` must free all allocated segment strings and the segment array itself
- `finalize()` must call `deinit()` then `bun.destroy(this)` to release the struct
- Cached property values for `pattern` and `paramNames` must use the generated cache accessors

### Error Handling

- All methods receiving arguments must validate argument count using `callFrame.arguments()`
- Missing required arguments must throw a descriptive error: `"Expected 1 argument, got 0"`
- Non-string arguments must throw: `"Expected string argument"`
- Type errors in the constructor pattern must throw with the specific issue (e.g., `"Invalid pattern: consecutive slashes"`)

### Expected Functionality

- `new URLPatternMatcher("/users/:id").match("/users/42")` returns `{ matched: true, params: { id: "42" } }`
- `new URLPatternMatcher("/users/:id").match("/posts/42")` returns `null`
- `new URLPatternMatcher("/users/:id").test("/users/42")` returns `true`
- `new URLPatternMatcher("/files/*path").match("/files/a/b/c.txt")` returns `{ matched: true, params: { path: "a/b/c.txt" } }`
- `new URLPatternMatcher("/users/:id").paramNames` returns `["id"]`
- `new URLPatternMatcher("/users/:id/posts/:postId").paramNames` returns `["id", "postId"]`
- `new URLPatternMatcher("")` throws an error about empty pattern
- `new URLPatternMatcher("/a//b")` throws an error about consecutive slashes
- `new URLPatternMatcher("/users/:")` throws an error about unnamed parameter

## Acceptance Criteria

- The `.classes.ts` file defines the class with constructor, `match`, `test`, `pattern`, and `paramNames` as specified
- The Zig implementation compiles successfully and is registered in `generated_classes_list.zig`
- Static path matching, named parameter extraction, and wildcard capture work correctly
- Pattern and paramNames getters return cached values derived from the compiled pattern
- Invalid patterns throw descriptive JavaScript errors from the constructor
- Missing or wrong-type arguments throw appropriate errors from each method
- `finalize()` properly cleans up all allocated memory
