# Task: Implement a Duration Parser JSC Class in Bun Using Zig Bindings

## Background

Bun (https://github.com/oven-sh/bun) uses a code generation system that bridges JavaScript classes with Zig implementations via `.classes.ts` definition files. A new `Duration` class is needed that parses ISO 8601 duration strings (e.g., `"P1Y2M3DT4H5M6S"`) and provides arithmetic operations, comparison, and serialization. The class must be defined in a `.classes.ts` file and fully implemented in Zig, following Bun's established binding patterns.

## Files to Create/Modify

- `src/bun.js/api/Duration.classes.ts` (create) — JavaScript interface definition for the `Duration` class using Bun's `define()` API, declaring constructor, prototype methods (`add`, `subtract`, `multiply`, `toSeconds`, `toISO`, `toString`), and prototype properties (`years`, `months`, `days`, `hours`, `minutes`, `seconds`)
- `src/bun.js/api/Duration.zig` (create) — Zig implementation of the `Duration` struct with constructor, all methods, property getters, memory management (`deinit`/`finalize`), and JSC interop
- `src/bun.js/bindings/generated_classes_list.zig` (modify) — Add `Duration` to the generated classes list so the code generator includes it
- `test/js/bun/duration.test.ts` (create) — JavaScript tests for the `Duration` class covering construction, arithmetic, comparison, serialization, and error handling

## Requirements

### Class Definition (`Duration.classes.ts`)

- Use `define()` with:
  - `name: "Duration"`
  - `constructor: true`
  - `JSType: "object"`
  - `finalize: true`
  - `proto` must include: `add` (args: 1), `subtract` (args: 1), `multiply` (args: 1), `toSeconds` (args: 0), `toISO` (args: 0), `toString` (args: 0), `compare` (args: 1)
  - Property getters: `years` (getter: true, cache: true), `months` (getter: true, cache: true), `days` (getter: true, cache: true), `hours` (getter: true, cache: true), `minutes` (getter: true, cache: true), `seconds` (getter: true, cache: true)

### Zig Implementation (`Duration.zig`)

- Struct fields: `years: i32`, `months: i32`, `days: i32`, `hours: i32`, `minutes: i32`, `seconds: f64`
- Reference the generated bindings: `pub const js = JSC.Codegen.JSDuration;` with `toJS`, `fromJS`, `fromJSDirect`
- `constructor(globalObject, callFrame)`:
  - If the first argument is a string, parse it as ISO 8601 duration (`PnYnMnDTnHnMnS`)
  - If the first argument is an object, extract `years`, `months`, `days`, `hours`, `minutes`, `seconds` properties
  - If the first argument is a number, treat it as total seconds
  - Return `bun.JSError` on invalid input with message `"Invalid duration format"`
- `add(this, globalObject, callFrame)` — Takes another Duration (from JS) and returns a new Duration with each component summed
- `subtract(this, globalObject, callFrame)` — Takes another Duration and returns a new Duration with each component subtracted
- `multiply(this, globalObject, callFrame)` — Takes a number and returns a new Duration with each component multiplied by that factor
- `toSeconds(this, globalObject, callFrame)` — Returns total seconds as `JSValue.jsNumber()`, computing `years*365.25*86400 + months*30.44*86400 + days*86400 + hours*3600 + minutes*60 + seconds`
- `toISO(this, globalObject, callFrame)` — Returns an ISO 8601 string like `"P1Y2M3DT4H5M6S"`, omitting zero-value components
- `toString` — Same as `toISO`
- `compare(this, globalObject, callFrame)` — Returns -1, 0, or 1 comparing `toSeconds()` values
- Property getters: `getYears`, `getMonths`, `getDays`, `getHours`, `getMinutes`, `getSeconds` — each returns the corresponding struct field as `JSValue.jsNumber()`
- `deinit` and `finalize` for proper memory cleanup using `bun.destroy(this)`

### ISO 8601 Parsing

- Must handle: `"P1Y"`, `"P2M"`, `"P3D"`, `"PT4H"`, `"PT5M"`, `"PT6S"`, `"PT6.5S"` (fractional seconds), `"P1Y2M3DT4H5M6S"` (full)
- The `T` separator is required before time components (H, M after T, S)
- Negative durations are supported via leading `-`: `"-P1D"` yields days = -1
- Invalid strings (e.g., `"hello"`, `"P"`, `"PT"`) must throw `"Invalid duration format"`

### Generated Classes Registration

- Add `Duration` to the `generated_classes_list.zig` array following the existing entry pattern

### Expected Functionality

- `new Duration("P1Y2M3DT4H5M6S")` creates a Duration with years=1, months=2, days=3, hours=4, minutes=5, seconds=6
- `new Duration(3661)` creates a Duration with seconds=3661
- `new Duration({hours: 2, minutes: 30})` creates a Duration with hours=2, minutes=30
- `d1.add(d2)` returns a new Duration with components summed
- `d.toISO()` returns `"P1Y2M3DT4H5M6S"` for a full duration
- `d.toISO()` returns `"PT1H"` when only hours are set (omits zero components)
- `d.toSeconds()` computes total seconds as a number
- `d.compare(d2)` returns -1 if `d` is shorter
- `new Duration("invalid")` throws `"Invalid duration format"`

## Acceptance Criteria

- `Duration.classes.ts` follows Bun's `define()` pattern with all required methods and properties
- The Zig implementation compiles as part of Bun's build pipeline via `bun run build`
- `Duration` is registered in `generated_classes_list.zig`
- ISO 8601 parsing correctly handles full, partial, and fractional-second duration strings
- Object and number constructor overloads work correctly
- Arithmetic methods (`add`, `subtract`, `multiply`) return new Duration instances (immutable pattern)
- `toISO()` omits zero-valued components and correctly places the `T` separator
- Property getters return the correct component values
- `finalize()` properly frees memory via `bun.destroy(this)`
- `python -m pytest /workspace/tests/test_implementing_jsc_classes_zig.py -v --tb=short` passes
