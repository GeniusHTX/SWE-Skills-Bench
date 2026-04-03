# Task: Implement a RingBuffer Class in Bun's Zig Runtime with JSC Bindings

## Background

Bun (https://github.com/oven-sh/bun) uses a `.classes.ts` and Zig implementation pattern to bridge JavaScript and native code through JavaScriptCore. The task is to implement a `RingBuffer` class — a fixed-capacity circular buffer for efficient byte streaming — as a native Bun API exposed to JavaScript.

## Files to Create/Modify

- `src/bun.js/api/RingBuffer.classes.ts` (create) — JavaScript class definition for JSC code generation
- `src/bun.js/api/RingBuffer.zig` (create) — Zig implementation of the ring buffer data structure and JSC method bindings
- `src/bun.js/bindings/generated_classes_list.zig` (modify) — Register `RingBuffer` in Bun's generated bindings list
- `test/js/bun/ringbuffer.test.ts` (create) — Unit tests covering all methods and edge cases

## Requirements

### Class Definition (`RingBuffer.classes.ts`)

Define the `RingBuffer` class with the following interface:

- **Constructor**: Takes a single argument `capacity` (positive integer, required)
- **Properties** (getters):
  - `capacity` — Returns the fixed maximum number of bytes the buffer can hold
  - `length` — Returns the current number of unread bytes in the buffer
  - `available` — Returns the number of bytes that can be written before the buffer is full
  - `isEmpty` — Returns `true` if the buffer contains no unread data
  - `isFull` — Returns `true` if the buffer has no available write space
- **Methods**:
  - `write(data: Uint8Array): number` — Writes bytes into the buffer; returns the number of bytes actually written (may be less than `data.length` if the buffer fills)
  - `read(length: number): Uint8Array` — Reads up to `length` bytes from the buffer; returns a `Uint8Array` containing the bytes read (may be shorter than `length` if fewer bytes are available)
  - `peek(length: number): Uint8Array` — Same as `read` but does not advance the read cursor
  - `clear(): void` — Resets the buffer to empty without deallocating memory
  - `toBytes(): Uint8Array` — Returns a copy of all unread data as a contiguous `Uint8Array`

### Zig Implementation (`RingBuffer.zig`)

- Allocate the internal buffer using `bun.default_allocator` in the constructor
- Free the internal buffer in `deinit`/`finalize`
- The ring buffer must use a head/tail pointer design: `write` advances the tail, `read` advances the head
- `write` must handle wrap-around (copying in two memcpy segments when the write spans the end of the internal array)
- `read` must handle wrap-around similarly
- If `write` is called when the buffer is full, it writes zero bytes and returns `0` (does not overwrite existing data)
- If `read` is called when the buffer is empty, it returns an empty `Uint8Array`
- All methods must validate arguments: `capacity` must be a positive integer (throw `TypeError` otherwise), `length` must be non-negative, `data` must be a `Uint8Array`
- The `peek` method must not modify the head pointer
- `toBytes` must return a contiguous copy even when the internal data wraps around the end of the buffer

### Error Handling

- Constructor with non-positive or non-integer capacity throws `TypeError: "capacity must be a positive integer"`
- `write` with a non-Uint8Array argument throws `TypeError: "data must be a Uint8Array"`
- `read` or `peek` with a negative length throws `RangeError: "length must be non-negative"`

### Registration

- Add `RingBuffer` to the generated classes list so the build system generates the necessary C++ and Zig binding glue code

## Expected Functionality

- `new RingBuffer(8)` creates a buffer that can hold 8 bytes
- Writing `[1, 2, 3, 4, 5]` into an 8-capacity buffer sets `length` to 5 and `available` to 3
- Reading 3 bytes returns `[1, 2, 3]` and sets `length` to 2
- Writing `[6, 7, 8, 9, 10, 11]` into the buffer with 5 available bytes writes only 5 bytes and returns `5`
- `peek(2)` returns the next 2 bytes without advancing the read position
- After `clear()`, `length` is 0, `isEmpty` is `true`, and `available` equals `capacity`
- Wrap-around: writing and reading across the end of the internal array produces correct contiguous output from `toBytes()`

## Acceptance Criteria

- The `RingBuffer` class is constructable from JavaScript with `new RingBuffer(capacity)`
- All five properties (`capacity`, `length`, `available`, `isEmpty`, `isFull`) return correct values after every operation
- `write` handles partial writes when the buffer has less available space than the input
- `read` and `peek` handle wrap-around reads correctly
- `toBytes` returns a contiguous copy of all unread data regardless of internal wrap state
- Invalid arguments throw the specified `TypeError` or `RangeError` with the specified messages
- Memory allocated in the constructor is freed when the object is garbage collected
- The project builds without errors after adding the new class to the generated classes list
