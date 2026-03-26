# Task: Implement JSC Class Bindings for a Zig-Based HTTP Headers Module in Bun

## Background

Bun (https://github.com/oven-sh/bun) is a JavaScript runtime built with Zig. Bun uses `.classes.ts` definition files to generate JavaScript-visible classes backed by Zig implementations. The project needs a new `HTTPHeaders` class that exposes efficient HTTP header manipulation to JavaScript via Bun's JSC (JavaScriptCore) binding system.

## Files to Create/Modify

- `src/bun.js/api/HTTPHeaders.classes.ts` (create) — Class definition file specifying the JavaScript interface, methods, getters, and constructor
- `src/bun.js/bindings/HTTPHeaders.zig` (create) — Zig implementation of the HTTPHeaders class with memory management
- `src/bun.js/bindings/http_headers_exports.zig` (create) — Export bindings connecting Zig functions to the JSC bridge
- `test/js/bun/http/headers.test.ts` (create) — JavaScript-side tests for the HTTPHeaders class

## Requirements

### Class Definition (.classes.ts)

- Define `HTTPHeaders` class in the `.classes.ts` file following Bun's class generation pattern:
  - Constructor: `constructor(init?: Record<string, string> | [string, string][])` — initialize from object or entries
  - Methods: `get(name: string): string | null`, `set(name: string, value: string): void`, `append(name: string, value: string): void`, `delete(name: string): boolean`, `has(name: string): boolean`, `entries(): [string, string][]`, `keys(): string[]`, `values(): string[]`
  - Getter: `count` — returns the number of unique header names
  - Method: `toJSON(): Record<string, string>` — serialize to a plain object
- Specify the Zig implementation file as the backing implementation
- Mark the class as `finalize`-aware for proper garbage collection cleanup

### Zig Implementation

- Implement the backing struct `HTTPHeaders` in Zig with:
  - Internal storage: a hash map mapping lowercase header names to a list of values (headers can have multiple values)
  - `init(allocator: std.mem.Allocator)` — initialize with a given allocator
  - `deinit()` — free all allocated memory (called during garbage collection finalization)
  - `get(name)` — return the first value for the header (case-insensitive name lookup), or null
  - `set(name, value)` — replace all values for the header with a single new value
  - `append(name, value)` — add a value to the header's value list (for headers like `Set-Cookie`)
  - `delete(name)` — remove the header entirely; return true if it existed
  - `has(name)` — return true if the header exists
- All header name lookups must be case-insensitive: store names in lowercase internally
- Header names must be validated: reject names containing characters outside `[a-zA-Z0-9!#$%&'*+\-.^_\`|~]` (RFC 7230 token characters); return error for invalid names
- Header values must not contain `\r` or `\n` characters; reject with error if they do

### Memory Management

- The Zig struct must track all allocations and free them in `deinit()`
- When `set()` replaces existing values, the old values must be freed
- When `delete()` removes a header, both the key and all values must be freed
- Use the allocator pattern (accept `std.mem.Allocator`) — do not use global allocators

### JSC Bridge (CallFrame Integration)

- Export functions use `CallFrame` to extract JavaScript arguments:
  - `callFrame.argument(0)` to get the first argument
  - Convert JSValue to Zig slice using `.toSlice(globalThis, allocator)`
  - Return JSValue using `.toJS()` for strings or `.jsBoolean()` for booleans
- Handle missing arguments gracefully: `get()` with no arguments returns null, `set()` with < 2 arguments throws a TypeError

### Expected Functionality

- `new HTTPHeaders({"Content-Type": "application/json"})` creates headers with one entry
- `headers.get("content-type")` returns `"application/json"` (case-insensitive)
- `headers.append("Set-Cookie", "a=1"); headers.append("Set-Cookie", "b=2")` stores both values
- `headers.get("Set-Cookie")` returns `"a=1"` (first value)
- `headers.entries()` returns `[["set-cookie", "a=1"], ["set-cookie", "b=2"]]` (all entries including duplicate names)
- `headers.delete("set-cookie")` returns true and removes both values
- `headers.count` returns the number of unique header names
- `new HTTPHeaders()` with an invalid header name `"Invalid Header"` (contains space) throws a TypeError
- Setting a value with `\n` in it throws a TypeError

## Acceptance Criteria

- `.classes.ts` file defines the HTTPHeaders class with all specified methods, getters, and constructor
- Zig implementation stores headers case-insensitively with support for multiple values per header name
- Header name validation rejects non-token characters per RFC 7230
- Header value validation rejects `\r` and `\n` characters
- `get()` returns the first value; `entries()` returns all values including duplicates
- `set()` replaces all values; `append()` adds a new value
- Memory management frees all allocations in `deinit()` and when values are replaced/deleted
- JSC bridge correctly handles argument extraction and type conversion
- Missing arguments throw TypeError with descriptive messages
- Tests cover construction, case-insensitive access, multi-value headers, deletion, validation errors, and edge cases
