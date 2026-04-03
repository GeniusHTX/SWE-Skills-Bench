# Task: Implement a JavaScript URL Pattern Matching Class in Bun Using Zig Bindings

## Background

Bun uses a `.classes.ts` definition file to declare JavaScript classes that are implemented in Zig and bridged to JavaScriptCore (JSC). A new `URLPattern` class is needed that provides URL pattern matching capabilities — parsing URL patterns with named parameters, matching URLs against patterns, and extracting captured groups. The class must be defined via the bindings generator and implemented in Zig.

## Files to Create/Modify

- `src/bun.js/api/URLPattern.classes.ts` (new) — Class definition file declaring the `URLPattern` class with constructor, methods, and properties for the bindings generator
- `src/bun.js/api/URLPattern.zig` (new) — Zig implementation of the `URLPattern` class with pattern parsing, URL matching, and group extraction
- `src/bun.js/api/URLPattern.test.ts` (new) — Test file exercising the URLPattern class from JavaScript

## Requirements

### Class Definition (.classes.ts)

- Define a class named `URLPattern` with `constructor: true`, `JSType: "object"`, and `finalize: true`
- Proto methods:
  - `test` — accepts 1 argument (URL string), returns boolean
  - `exec` — accepts 1 argument (URL string), returns object or null
- Proto getters with `cache: true`:
  - `protocol` — returns the pattern's protocol component
  - `hostname` — returns the pattern's hostname component
  - `pathname` — returns the pattern's pathname component
  - `search` — returns the pattern's search component
  - `hash` — returns the pattern's hash component

### Constructor Behavior

- `new URLPattern(pattern)` where `pattern` is a string in the format `"protocol://hostname/pathname?search#hash"` with named parameters (`:paramName`) and wildcards (`*`)
- `new URLPattern({ protocol, hostname, pathname, search, hash })` where each field is an optional pattern string
- If no arguments are provided or the pattern is invalid (unmatched braces, empty parameter names), throw a `TypeError` with message "Invalid URL pattern"
- Named parameters are segments starting with `:` followed by alphanumeric characters (e.g., `:id`, `:slug`)
- Wildcards `*` match any non-empty sequence of characters

### Pattern Matching (`test` method)

- `test(url)` returns `true` if the URL matches the pattern, `false` otherwise
- Matching is component-wise: protocol, hostname, pathname, search, and hash are matched independently
- Components not specified in the pattern match any value (treated as wildcard)
- Named parameters (`:param`) in pathname match a single path segment (between `/` characters)
- Wildcard `*` in pathname matches one or more path segments
- Matching is case-insensitive for protocol and hostname, case-sensitive for pathname, search, and hash
- If `url` is not a valid URL string, return `false` (do not throw)

### Result Extraction (`exec` method)

- `exec(url)` returns `null` if the URL does not match the pattern
- If the URL matches, returns an object with component results: `{ protocol: { input, groups }, hostname: { input, groups }, pathname: { input, groups }, search: { input, groups }, hash: { input, groups } }`
- `input` is the matched component string from the URL
- `groups` is an object mapping named parameter names to their captured values (e.g., `{ id: "42", slug: "hello-world" }`)
- Components without named parameters have an empty `groups` object
- Wildcard captures are stored under the key `"0"` in groups

### Zig Implementation

- Store parsed pattern components as Zig structs with segment arrays (literal segments and parameter segments)
- Use `bun.new()` for allocation and implement `finalize` for cleanup via `deinit`
- Use `JSC.JSValue.jsString` for returning string values and `JSC.JSValue.createEmptyObject` for building result objects
- Getter methods must use the `cache: true` flag in the class definition and return cached `JSC.JSValue` strings

### Expected Functionality

- `new URLPattern("/users/:id")` → `test("/users/42")` returns `true`; `exec("/users/42")` returns pathname groups `{ id: "42" }`
- `new URLPattern("/users/:id/posts/:postId")` → `exec("/users/5/posts/99")` returns pathname groups `{ id: "5", postId: "99" }`
- `new URLPattern("/files/*")` → `test("/files/docs/readme.md")` returns `true`; `exec("/files/docs/readme.md")` returns pathname groups `{ "0": "docs/readme.md" }`
- `new URLPattern({ protocol: "https", hostname: "*.example.com" })` → `test("https://api.example.com/anything")` returns `true`
- `new URLPattern("/users/:id")` → `test("/posts/42")` returns `false`
- `new URLPattern("/users/:id")` → `test("not-a-url")` returns `false`
- `new URLPattern("")` → throws `TypeError: Invalid URL pattern`
- `urlPattern.pathname` getter returns the pattern's pathname string (e.g., `"/users/:id"`)

## Acceptance Criteria

- The `.classes.ts` file correctly defines `URLPattern` with constructor, `test`, `exec`, getters, and `finalize`
- The Zig implementation parses URL patterns with named parameters and wildcards
- `test()` correctly matches URLs component-wise with case rules and returns `false` for non-matching or invalid URLs
- `exec()` returns structured result objects with captured groups for each URL component, or `null` for non-matches
- Named parameters capture single path segments; wildcards capture one or more segments
- The constructor validates patterns and throws `TypeError` for invalid input
- Getters return cached pattern component strings
- `bun run build` compiles the new class without errors
- Tests verify matching, non-matching, parameter extraction, wildcard capture, multi-component patterns, and error cases
