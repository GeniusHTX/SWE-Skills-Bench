# Task: Add a Flame Graph Collapse Formatter to py-spy

## Background

py-spy (https://github.com/benfred/py-spy) is a sampling profiler for Python programs written in Rust. A new output formatter is needed that converts captured stack traces into the "collapsed stack" format used by flame graph tools, enabling users to pipe py-spy output directly into flame graph generators.

## Files to Create/Modify

- `src/flamegraph_collapsed.rs` (create) — Collapsed stack format output module
- `src/main.rs` (modify) — Register the collapsed format formatter in CLI output options

## Requirements

### Collapsed Format

- Convert sampled stack traces into the collapsed format: `function1;function2;function3 count`
- Each line represents a unique stack trace with its sample count
- Function names should include module/file information (e.g., `module.py:function_name`)

### Filtering

- Support filtering stacks by minimum sample count (ignore stacks with fewer than N samples)
- Support excluding frames matching a configurable pattern (e.g., exclude internal Python frames)
- Support limiting output to the top N most frequent stacks

### Integration

- Register the formatter within py-spy's output system so it can be selected via command-line options
- Accept configuration parameters (minimum count, exclusion patterns, top N) from the calling code

### Build

- All Rust source files must compile as part of the py-spy project

## Expected Functionality

- Profiling data can be output in collapsed stack format suitable for flame graph generation
- Filtering reduces noise by removing low-frequency and internal stacks
- The formatter integrates with py-spy's existing output infrastructure

## Acceptance Criteria

- The profiler can emit sampled stack traces in collapsed-stack format suitable for downstream flame graph tools.
- Repeated identical stacks are aggregated into a single line with an accurate sample count.
- Filtering options can exclude low-frequency stacks, remove unwanted frames, and limit the output to the most important stacks.
- The formatter integrates into the existing output-selection flow rather than existing as an isolated helper.
- Function names in the output preserve enough file or module context to make flame graph analysis useful.
