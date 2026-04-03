# Task: Implement a CacheMap JSC Class in Bun Using Zig

## Background

Bun (https://github.com/oven-sh/bun) bridges JavaScript and Zig through its JavaScriptCore (JSC) bindings generator. New JS-visible classes are defined in `.classes.ts` files and implemented in Zig. A `CacheMap` class is needed — a fixed-capacity key-value store with LRU eviction that is exposed to JavaScript. This class requires a `.classes.ts` interface definition and a corresponding Zig implementation.

## Files to Create/Modify

- `src/bun.js/api/CacheMap.classes.ts` (create) — JSC class definition specifying the constructor, methods, and properties for `CacheMap`.
- `src/bun.js/bindings/CacheMap.zig` (create) — Zig implementation of the `CacheMap` class, including the LRU data structure, constructor, and all methods.
- `src/bun.js/bindings/generated.zig` (modify) — Register the new `CacheMap` binding entry so the code-generation pipeline picks it up.

## Requirements

### Class Definition (`.classes.ts`)

- Export a class named `CacheMap`.
- Constructor accepts one argument: `capacity` (positive integer, required).
- Methods:
  - `get(key: string) → string | undefined` — Returns the cached value or `undefined` if not present.
  - `set(key: string, value: string) → void` — Inserts or updates an entry; if the cache is at capacity, the least-recently-used entry is evicted first.
  - `delete(key: string) → boolean` — Removes an entry; returns `true` if it existed.
  - `clear() → void` — Removes all entries.
- Properties:
  - `size` (getter, read-only) — Returns the current number of entries.
  - `capacity` (getter, read-only) — Returns the maximum capacity set at construction.

### Zig Implementation

- Maintain an internal hash map and a doubly-linked list (or equivalent) to track access order.
- `get` must promote the accessed entry to the most-recently-used position.
- `set` must insert at the most-recently-used position; if at capacity, evict the least-recently-used entry before inserting.
- All string keys and values passed from JavaScript must be properly extracted from the `JSValue` / `CallFrame` and must not leak memory when entries are evicted or deleted.
- The `finalize` callback must free all heap-allocated memory when the JavaScript object is garbage collected.

### Edge Cases

- Constructing with `capacity = 0` should throw a `RangeError` in JavaScript.
- Constructing with a non-integer or negative value should throw a `TypeError`.
- `get` / `delete` on a non-existent key must not crash; `get` returns `undefined`, `delete` returns `false`.
- `set` with the same key twice updates the value in place and promotes it without changing the `size`.
- Calling `clear` on an already-empty cache is a no-op.

### Expected Functionality

- `const c = new CacheMap(2); c.set("a","1"); c.set("b","2"); c.get("a"); c.set("c","3");` → key `"b"` is evicted (LRU), `c.get("b")` returns `undefined`, `c.size` is `2`.
- `new CacheMap(0)` → throws `RangeError`.
- `c.delete("a")` returns `true`; `c.delete("a")` again returns `false`.
- After `c.clear()`, `c.size` is `0` and `c.get("a")` returns `undefined`.

## Acceptance Criteria

- The `.classes.ts` file exports a valid class definition that the Bun codegen pipeline can process.
- The Zig implementation compiles without errors as part of `bun run build`.
- `CacheMap` is accessible from JavaScript via `new CacheMap(capacity)`.
- LRU eviction removes the least-recently-used entry when capacity is exceeded.
- `get` promotes entries to most-recently-used; repeated `set` on the same key updates in place.
- Invalid constructor arguments (`0`, negative, non-integer) throw appropriate JavaScript exceptions.
- Memory is properly freed on `delete`, `clear`, eviction, and garbage collection (no leaks observable under `--expose-gc` testing).
