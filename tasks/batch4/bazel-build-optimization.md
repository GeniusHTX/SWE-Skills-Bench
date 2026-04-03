# Task: Configure Bazel Build Infrastructure with Remote Caching and Custom Rules for a Python Monorepo

## Background

The Bazel repository (https://github.com/bazelbuild/bazel) is a build system for multi-language monorepos. A new example Python project is needed that demonstrates an optimized Bazel configuration including a WORKSPACE setup with rules_python, a `.bazelrc` with performance and CI profiles, a custom macro for generating Python library+test pairs, remote cache configuration, and build targets covering a library, binary, and test suite.

## Files to Create/Modify

- `examples/python-bazel/WORKSPACE.bazel` (create) — Workspace with rules_python and pip dependencies
- `examples/python-bazel/.bazelrc` (create) — Build profiles for local, CI, and remote cache configurations
- `examples/python-bazel/BUILD.bazel` (create) — Root BUILD file with visibility defaults
- `examples/python-bazel/src/lib/BUILD.bazel` (create) — Library build targets for core modules
- `examples/python-bazel/src/lib/calculator.py` (create) — Calculator module with basic operations
- `examples/python-bazel/src/lib/formatter.py` (create) — Output formatter module
- `examples/python-bazel/src/app/BUILD.bazel` (create) — Binary target for the CLI application
- `examples/python-bazel/src/app/main.py` (create) — CLI entry point using the library
- `examples/python-bazel/tests/BUILD.bazel` (create) — Test targets
- `examples/python-bazel/tests/test_calculator.py` (create) — Unit tests for calculator
- `examples/python-bazel/tests/test_formatter.py` (create) — Unit tests for formatter
- `examples/python-bazel/tools/macros.bzl` (create) — Custom Starlark macro `py_library_with_tests` that generates a `py_library` and `py_test` target pair
- `examples/python-bazel/requirements.txt` (create) — Python dependencies

## Requirements

### WORKSPACE.bazel

- Workspace name: `python_bazel_demo`
- Load `rules_python` via `http_archive` (version 0.27.0 or later)
- Configure Python toolchain for Python 3.11
- Use `pip_parse` to create a pip repository from `requirements.txt`
- Load pip dependencies via `install_deps` from the parsed repository

### .bazelrc

- **Default profile**: `--enable_platform_specific_config`, Kryo-style optimizations where applicable, `--jobs=auto`, `--local_cpu_resources=HOST_CPUS*.75`
- **Disk cache profile** (`--config=cache`): `--disk_cache=~/.cache/bazel-disk`, `--repository_cache=~/.cache/bazel-repo`
- **Remote cache profile** (`--config=remote-cache`): `--remote_cache=grpcs://cache.example.com`, `--remote_upload_local_results=true`, `--remote_timeout=3600`
- **CI profile** (`--config=ci`): inherit remote-cache, `--build_metadata=ROLE=CI`, `--color=no`, `--curses=no`
- **Test settings**: `--test_output=errors`, `--test_summary=detailed`
- **Coverage settings**: `--combined_report=lcov`, `--instrumentation_filter="//..."`

### Build Targets

**Library** (`src/lib/`):
- `py_library` target `calculator` with srcs `calculator.py`, visibility `["//visibility:public"]`
- `py_library` target `formatter` with srcs `formatter.py`, deps on `calculator`

**Binary** (`src/app/`):
- `py_binary` target `app` with srcs `main.py`, deps on `//src/lib:calculator` and `//src/lib:formatter`

**Tests** (`tests/`):
- `py_test` target `test_calculator` with srcs `test_calculator.py`, deps on `//src/lib:calculator`, size `"small"`
- `py_test` target `test_formatter` with srcs `test_formatter.py`, deps on `//src/lib:formatter`, size `"small"`

### Custom Macro (tools/macros.bzl)

- `py_library_with_tests(name, srcs, deps=[], test_srcs=[], test_deps=[], **kwargs)`:
  - Generates a `py_library` with name `name`, srcs `srcs`, deps `deps`
  - Generates a `py_test` with name `name + "_test"`, srcs `test_srcs`, deps `[":"+name] + test_deps`, size `"small"`
  - If `test_srcs` is empty, skip the test target generation

### Calculator Module

- Functions: `add(a, b)`, `subtract(a, b)`, `multiply(a, b)`, `divide(a, b)`
- `divide` must raise `ValueError` on division by zero (not `ZeroDivisionError`) with message "Cannot divide by zero"
- All functions accept int or float arguments and return float

### Formatter Module

- `format_result(operation: str, a, b, result) -> str` — returns `"{a} {operation} {b} = {result}"` (e.g., `"3 + 4 = 7.0"`)
- `format_table(results: list[tuple]) -> str` — formats a list of (operation, a, b, result) tuples into an aligned ASCII table with headers

### Expected Functionality

- `bazel build //...` builds all targets successfully
- `bazel test //...` runs all tests successfully
- `bazel run //src/app:app` executes the CLI application
- `bazel build --config=cache //...` enables disk caching
- The custom macro creates both library and test targets from a single declaration

## Acceptance Criteria

- WORKSPACE.bazel correctly loads rules_python and configures the Python toolchain
- .bazelrc contains valid profiles for default, cache, remote-cache, and CI configurations
- All `py_library`, `py_binary`, and `py_test` targets have correct srcs and deps
- The custom `py_library_with_tests` macro generates both targets correctly and skips tests when no test_srcs are provided
- Calculator functions handle edge cases (division by zero) properly
- `bazel build //...` completes without errors
- All `bazel test //...` tests pass
