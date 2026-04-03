# Task: Implement a BunCronJob JSC Class with Zig Bindings

## Background

The Bun runtime (https://github.com/oven-sh/bun) exposes JavaScript APIs by defining class interfaces in `.classes.ts` files and implementing them in Zig, which are then bridged to JavaScriptCore (JSC) via code generation. A new `Bun.CronJob` class is needed to allow users to schedule recurring tasks from JavaScript using cron expressions. This class must be defined through Bun's bindings generator and fully implemented in Zig.

## Files to Create/Modify

- `src/bun.js/api/bun/cron.classes.ts` (create) — JSC class definition for `CronJob` using the `define()` interface
- `src/bun.js/api/bun/cron.zig` (create) — Zig implementation of the `CronJob` struct with constructor, methods, getters, and lifecycle management
- `src/bun.js/bindings/generated_classes_list.zig` (modify) — Register the new `CronJob` class so the code generator includes it
- `src/bun.js/api/bun.zig` (modify) — Export the `CronJob` binding to the `Bun` global namespace so it is accessible as `new Bun.CronJob(...)`

## Requirements

### Class Definition (`.classes.ts`)

- The class must be named `CronJob`.
- It must have a public constructor accepting two arguments: a cron expression string and a callback function.
- It must define the following prototype methods:
  - `start()` — begins scheduling the cron job
  - `stop()` — cancels the scheduled cron job
  - `nextRun()` — returns a `Date` representing the next scheduled execution time
- It must define the following prototype getters:
  - `expression` — returns the cron expression string (cached)
  - `running` — returns a boolean indicating whether the job is active
- The class must set `finalize: true` to enable garbage-collection cleanup.

### Zig Implementation

- The `CronJob` struct must store the cron expression (as a `[]const u8`), a reference to the JS callback function, and a boolean `is_running` flag.
- The `constructor` function must validate that the first argument is a string and the second argument is callable; throw a `TypeError` via `globalObject.throw(...)` with a descriptive message if either check fails.
- The `start` method must set `is_running` to `true` and return `undefined`.
- The `stop` method must set `is_running` to `false` and return `undefined`.
- The `nextRun` method must return a JS `Date` object. If the cron expression cannot be parsed, it must throw a `RangeError` with the message `"Invalid cron expression"`.
- The `getExpression` getter must return the stored expression string and use the cached value mechanism from the generated bindings.
- The `getRunning` getter must return `JSValue.jsBoolean(this.is_running)`.
- The `finalize` function must call `deinit` and then `bun.destroy(this)`.
- The `deinit` function must release any allocated memory for the stored expression.

### Error Handling

- `constructor` with zero arguments → `TypeError: CronJob requires a cron expression string and a callback function`
- `constructor` with a non-string first argument → `TypeError: First argument must be a cron expression string`
- `constructor` with a non-function second argument → `TypeError: Second argument must be a callback function`
- `nextRun()` on an instance with an unparseable expression like `"not a cron"` → `RangeError: Invalid cron expression`

### Registration

- The new class must be added to the generated classes list so the code generator produces the C++ and Zig binding glue.
- The class must be accessible as `Bun.CronJob` from JavaScript (i.e., attached to the `Bun` global object).

### Expected Functionality

- `const job = new Bun.CronJob("*/5 * * * *", () => console.log("tick"))` → creates a `CronJob` instance without error.
- `job.expression` → returns `"*/5 * * * *"`.
- `job.running` → returns `false` before `start()` is called.
- `job.start(); job.running` → returns `true`.
- `job.stop(); job.running` → returns `false`.
- `job.nextRun()` → returns a `Date` object representing a future timestamp.
- `new Bun.CronJob(123, () => {})` → throws `TypeError`.
- `new Bun.CronJob("* * * * *")` → throws `TypeError` (missing callback).

## Acceptance Criteria

- A `.classes.ts` file defines the `CronJob` class interface with constructor, three methods (`start`, `stop`, `nextRun`), and two getters (`expression`, `running`).
- A Zig file implements the `CronJob` struct with all required methods, getters, constructor validation, error handling, and memory cleanup.
- The class is registered in `generated_classes_list.zig` and exposed on the `Bun` global object.
- Constructing with valid arguments succeeds; constructing with missing or invalid arguments throws the specified `TypeError` messages.
- `start()` / `stop()` toggle the `running` state correctly.
- `nextRun()` returns a JS Date for a valid cron expression and throws `RangeError` for an invalid one.
- The `finalize` method properly releases allocated resources to prevent memory leaks.
- The build command `bun run build` completes without errors.
