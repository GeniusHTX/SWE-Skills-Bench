# Task: Implement a URLPattern Class Binding in Bun's Zig-JSC Bridge

## Background

Bun's JavaScript runtime uses a code generation pipeline that bridges JavaScript classes to Zig implementations via `.classes.ts` definition files. A new `URLPattern` class needs to be added that allows JavaScript code to construct URL pattern matchers, test URLs against patterns, and extract named groups from matched URLs. This requires defining the JavaScript interface in a `.classes.ts` file, implementing the backing logic in Zig, and registering the class in the generated classes list.

## Files to Create/Modify

- `src/bun.js/url_pattern.classes.ts` (create) — JavaScript class interface definition for `URLPattern`
- `src/bun.js/bindings/URLPattern.zig` (create) — Zig implementation of the `URLPattern` class with constructor, methods, getters, and lifecycle management
- `src/bun.js/bindings/generated_classes_list.zig` (modify) — Register `URLPattern` in the generated classes list
- `test/js/bun/url_pattern.test.ts` (create) — Unit tests exercising construction, matching, named groups, and error handling

## Requirements

### Class Definition (url_pattern.classes.ts)

- Class name: `URLPattern`
- `constructor: true` — accepts pattern arguments from JavaScript
- `finalize: true` — must release Zig-allocated memory when garbage collected
- `JSType: "object"`
- Prototype methods:
  - `test` with 1 argument — returns boolean indicating whether a URL matches
  - `exec` with 1 argument — returns match result object or null
- Prototype getters (all with `cache: true`):
  - `protocol` — returns the protocol component pattern
  - `hostname` — returns the hostname component pattern
  - `pathname` — returns the pathname component pattern
  - `search` — returns the search component pattern
  - `hash` — returns the hash component pattern

### Zig Implementation (URLPattern.zig)

- Struct `URLPattern` with fields: `protocol`, `hostname`, `pathname`, `search`, `hash` (all `[]const u8`), and a compiled state field
- Public const declarations: `js = JSC.Codegen.JSURLPattern`, `toJS = js.toJS`, `fromJS = js.fromJS`, `fromJSDirect = js.fromJSDirect`
- `constructor(globalObject: *JSGlobalObject, callFrame: *JSC.CallFrame) bun.JSError!*URLPattern`:
  - Must read arguments from `callFrame.arguments()`
  - If zero arguments provided, return `globalObject.throw("URLPattern constructor requires at least 1 argument", .{})`
  - First argument: when it is a string, parse it as a full URL pattern; when it is an object, read `protocol`, `hostname`, `pathname`, `search`, `hash` properties from it
  - Allocate with `bun.new(URLPattern, .{ ... })` or `URLPattern.new(...)`
- `test(this: *URLPattern, globalObject: *JSGlobalObject, callFrame: *JSC.CallFrame) bun.JSError!JSC.JSValue`:
  - If argument count < 1 or first argument is undefined/null, return `globalObject.throw("test() requires a URL string argument", .{})`
  - Compare URL components against stored patterns
  - Return `JSC.JSValue.jsBoolean(matched)`
- `exec(this: *URLPattern, globalObject: *JSGlobalObject, callFrame: *JSC.CallFrame) bun.JSError!JSC.JSValue`:
  - If no match, return `JSC.JSValue.jsNull()`
  - If match, construct and return a JS object with keys `protocol`, `hostname`, `pathname`, `search`, `hash`, each containing `input` and `groups` sub-objects
- Getters `getProtocol`, `getHostname`, `getPathname`, `getSearch`, `getHash`:
  - Each returns `JSC.JSValue.createStringFromUTF8(globalObject, this.<field>)`
  - Values are cached by the generated code due to `cache: true` in the definition
- `deinit(this: *URLPattern) void`:
  - Free all allocated `[]const u8` fields using `bun.default_allocator.free()`
- `finalize(this: *URLPattern) void`:
  - Call `this.deinit()` then `bun.destroy(this)`

### Registration

- Add `URLPattern` entry to `src/bun.js/bindings/generated_classes_list.zig` following the existing pattern of other class entries in that file

### Expected Functionality

- `new URLPattern({ pathname: "/users/:id" })` → constructs without error; `.pathname` getter returns `"/users/:id"`
- `new URLPattern({ pathname: "/users/:id" }).test("https://example.com/users/42")` → returns `true`
- `new URLPattern({ pathname: "/users/:id" }).test("https://example.com/posts/42")` → returns `false`
- `new URLPattern({ pathname: "/users/:id" }).exec("https://example.com/users/42")` → returns object with `pathname.groups.id === "42"`
- `new URLPattern({ pathname: "/users/:id", protocol: "https" }).test("http://example.com/users/42")` → returns `false` (protocol mismatch)
- `new URLPattern({ hostname: "*.example.com" }).test("https://sub.example.com/")` → returns `true`
- `new URLPattern()` → throws TypeError: "URLPattern constructor requires at least 1 argument"
- `new URLPattern({ pathname: "/users/:id" }).test()` → throws TypeError: "test() requires a URL string argument"
- `new URLPattern({ pathname: "/users/:id" }).exec("https://example.com/posts/1")` → returns `null`
- After garbage collection, no memory leaks from URLPattern instances (finalize is called)

### Memory Management

- All string fields stored in the struct must be allocated via `bun.default_allocator` and freed in `deinit`
- `finalize` must call `deinit` before `bun.destroy(this)` to prevent double-free
- Cached getter values use the generated `WriteBarrier` mechanism — the Zig code only computes the value on first access

## Acceptance Criteria

- `bun run build` completes without compilation errors (L1)
- `bun test test/js/bun/url_pattern.test.ts` passes all tests (L2)
- The `.classes.ts` definition generates valid C++ and Zig binding files without manual edits to generated code
- The constructor handles both string and object argument forms
- `test()` returns correct booleans for matching and non-matching URLs across protocol, hostname, pathname, search, and hash components
- `exec()` returns structured match objects with correctly extracted named groups, or `null` for non-matches
- All getters return the original pattern component strings and are cached after first access
- Missing or invalid arguments to constructor/test/exec produce thrown JavaScript errors, not Zig panics
- `finalize` properly frees all allocated memory without use-after-free or double-free
