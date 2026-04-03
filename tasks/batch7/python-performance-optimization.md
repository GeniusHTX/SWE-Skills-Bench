# Task: Add a Sampling Profiler Command to py-spy

## Background

py-spy (https://github.com/benfred/py-spy) is a Rust-based sampling profiler for Python processes. The task is to add a new `summary` subcommand that attaches to a running Python process, samples the call stack at a configurable rate for a fixed duration, and outputs a plain-text performance summary sorted by inclusive sample count — without writing a flamegraph or trace file.

## Files to Create/Modify

- `src/summary.rs` (create) — `SummaryRecorder` struct that collects samples and produces a call stack frequency report
- `src/main.rs` (modify) — Add the `summary` subcommand and its CLI argument parsing using the existing `clap` configuration
- `src/bin/py_spy.rs` (modify, if present) — Route the `summary` subcommand to `run_summary()`
- `tests/test_summary.py` (create) — Python integration tests that run `py-spy summary` on a synthetic target script and verify the output format

## Requirements

### `SummaryRecorder` (`src/summary.rs`)

```rust
use std::collections::HashMap;

pub struct FrameSummary {
    pub function: String,
    pub filename: String,
    pub lineno: u32,
    pub total_samples: u64,    // Samples where this frame appeared anywhere in the stack
    pub self_samples: u64,     // Samples where this frame was the topmost (on-CPU) frame
}

pub struct SummaryRecorder {
    samples: HashMap<String, FrameSummary>,  // key: "function (filename:lineno)"
    total_samples: u64,
    sample_rate: u64,          // Hz
    duration_secs: f64,
}

impl SummaryRecorder {
    pub fn new(sample_rate: u64) -> Self;
    
    /// Record one sampled call stack (ordered from innermost to outermost frame)
    pub fn record(&mut self, stack: &[py_spy::StackFrame]);
    
    /// Return frames sorted by total_samples descending
    pub fn top_frames(&self, limit: usize) -> Vec<&FrameSummary>;
    
    /// Render the summary as a formatted text table  
    pub fn render(&self, limit: usize) -> String;
    
    pub fn total_samples(&self) -> u64;
}
```

#### `record(stack)` Logic

For each frame in `stack`:
- Increment `total_samples` for that frame's entry in `self.samples`
- Increment `self_samples` only for the first (innermost/topmost) frame
- The key format: `"<function> (<filename>:<lineno>)"`

#### `render(limit)` Output Format

```
py-spy summary -- pid: 12345 | duration: 10s | rate: 100Hz | total samples: 1000

  %Self   Total   Self  Function (file:line)
 ─────────────────────────────────────────────────────────────
  45.2%   100.0%   452  slow_loop (target.py:15)
  12.3%    78.5%   123  compute_values (math_utils.py:42)
   8.1%    21.2%    81  json.loads (<frozen json/__init__>:341)
  ...

  * Showing top 20 results. Total: 1000 samples over 10.0s
```

Column definitions:
- `%Self`: `self_samples / total_samples * 100`
- `Total`: `total_samples / self.total_samples * 100` (inclusive %)
- `Self`: raw `self_samples` count
- `Function (file:line)`: key string

### `summary` Subcommand CLI

Add to the `clap` CLI in `main.rs` alongside the existing `record`, `dump`, `top` subcommands:

```rust
// Usage: py-spy summary --pid <PID> [--duration <SECS>] [--rate <HZ>] [--top <N>] [--nonblocking]
```

Arguments:
| Argument | Type | Default | Description |
|---|---|---|---|
| `--pid` / `-p` | u32 | required | PID of the target Python process |
| `--duration` / `-d` | u64 | 10 | How many seconds to sample |
| `--rate` / `-r` | u64 | 100 | Samples per second |
| `--top` / `-t` | usize | 20 | How many top frames to display |
| `--nonblocking` | flag | false | Use non-blocking mode (may miss samples but won't pause the target) |

#### Command Handler: `run_summary()`

1. Attach to the target process via `PythonSpy::new(pid, &config)?`
2. Create a `SummaryRecorder::new(rate)`
3. Loop for `duration` seconds: call `sampler.get_stack_traces()`, for each thread call `recorder.record()`
4. Sleep `1000ms / rate` between samples
5. At the end, call `recorder.render(top)` and print to stdout
6. Return `Ok(())`

### Integration Tests (`tests/test_summary.py`)

Create a target script `tests/data/summary_target.py`:
```python
import time

def busy_loop():
    total = 0
    for i in range(10**7):
        total += i
    return total

def main():
    for _ in range(100):
        busy_loop()
    time.sleep(30)  # Keep alive for profiling

if __name__ == "__main__":
    main()
```

Test cases:
1. Run `py-spy summary --pid <pid> --duration 3 --rate 50` against the target and verify:
   - Exit code is 0
   - Output contains `"Function (file:line)"` header
   - Output contains `"busy_loop"` in the results (it's the hot function)
   - Output contains `"total samples:"` in the footer
2. Test `--top 5` limits output to 5 frames
3. Test invalid PID returns non-zero exit code and prints an error

## Expected Functionality

- After profiling a tight loop for 3 seconds at 100Hz: `SummaryRecorder` has ~300 total samples
- The topmost frame in the tight loop function has `self_samples` close to `total_samples`
- `render()` produces a right-aligned percentage table with `%Self`, `Total`, `Self`, and `Function` columns
- `cargo build --release` completes successfully with the new `summary.rs` and modified `main.rs`

## Acceptance Criteria

- `SummaryRecorder::record()` correctly increments `total_samples` for all frames and `self_samples` only for the innermost frame
- `top_frames(n)` returns frames sorted by `total_samples` descending, limited to `n`
- `render()` produces the correct column headers and formatted rows
- `summary` subcommand is registered in the CLI with all five arguments
- `run_summary()` loops for exactly `duration` seconds and outputs the rendered report
- `cargo build --release` succeeds after changes
- Integration tests pass: `busy_loop` appears in output, `--top 5` limits rows, invalid PID returns error
