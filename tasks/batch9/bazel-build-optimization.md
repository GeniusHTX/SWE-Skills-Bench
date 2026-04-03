# Task: Create a Bazel Build Configuration for a Python Monorepo with Remote Caching

## Background

Bazel (https://github.com/bazelbuild/bazel) is a build system for large-scale monorepos. A complete Bazel build configuration is needed for a Python monorepo containing two applications (a web API server and a data pipeline CLI) and three shared libraries (core, models, utils), with proper BUILD files, dependency management, test configuration, custom macros, and remote cache configuration optimized for CI performance.

## Files to Create/Modify

- `examples/python-bazel/WORKSPACE.bazel` (create) — Workspace setup with `rules_python`, Python toolchain registration, `pip_parse` for external dependencies from `requirements_lock.txt`
- `examples/python-bazel/.bazelrc` (create) — Build flags: remote caching config, test output settings, Python version selection, CI-specific config group
- `examples/python-bazel/BUILD.bazel` (create) — Root BUILD file with `pip_parse` exports and workspace-level test suite
- `examples/python-bazel/requirements_lock.txt` (create) — Pinned pip dependencies: `flask==3.0.0`, `click==8.1.7`, `pydantic==2.5.0`, `pytest==7.4.3`, `requests==2.31.0`
- `examples/python-bazel/apps/api/BUILD.bazel` (create) — `py_binary` for the Flask API server with deps on `//libs/core`, `//libs/models`, pip flask
- `examples/python-bazel/apps/api/main.py` (create) — Flask app entry point with 2 endpoints: `GET /health` and `GET /api/items`
- `examples/python-bazel/apps/pipeline/BUILD.bazel` (create) — `py_binary` for the data pipeline CLI with deps on `//libs/core`, `//libs/utils`, pip click
- `examples/python-bazel/apps/pipeline/main.py` (create) — Click CLI with `process` and `validate` commands
- `examples/python-bazel/libs/core/BUILD.bazel` (create) — `py_library` for core module with `visibility = ["//apps:__subpackages__"]`
- `examples/python-bazel/libs/core/__init__.py` (create) — Core module with `Config` class and `get_version()` function
- `examples/python-bazel/libs/models/BUILD.bazel` (create) — `py_library` with dep on `//libs/core` and pip pydantic
- `examples/python-bazel/libs/models/__init__.py` (create) — Pydantic models: `Item(id, name, price)`, `ItemList(items, total)`
- `examples/python-bazel/libs/utils/BUILD.bazel` (create) — `py_library` with dep on `//libs/core`
- `examples/python-bazel/libs/utils/__init__.py` (create) — Utility functions: `slugify(text)`, `chunk_list(items, size)`, `retry(fn, max_retries)`
- `examples/python-bazel/tests/BUILD.bazel` (create) — `py_test` targets for core, models, utils, and integration tests
- `examples/python-bazel/tests/test_core.py` (create) — Tests for core Config and get_version
- `examples/python-bazel/tests/test_models.py` (create) — Tests for Pydantic models validation
- `examples/python-bazel/tests/test_utils.py` (create) — Tests for utility functions
- `examples/python-bazel/tools/BUILD.bazel` (create) — Custom Bazel macro `py_service` that wraps `py_binary` with standard test and lint targets

## Requirements

### WORKSPACE.bazel

- Load `rules_python` version 0.27.0 via `http_archive`
- Register Python 3.11 toolchain using `python_register_toolchains`
- Use `pip_parse` to install pip dependencies from `requirements_lock.txt`
- Load and call `install_deps()` from the generated pip repository
- Set workspace name to `"python_bazel_monorepo"`

### .bazelrc

- `build --incompatible_strict_action_env` for reproducible builds
- `build --symlink_prefix=dist/` to keep output predictable
- `test --test_output=errors` for concise test output
- `test --test_verbose_timeout_warnings` for slow test detection
- Config group `--config=ci`:
  - `build:ci --remote_cache=grpc://localhost:9092` (placeholder remote cache address)
  - `build:ci --google_default_credentials=false`
  - `build:ci --jobs=4`
  - `build:ci --noremote_upload_local_results` (read-only cache for CI)
- Config group `--config=debug`:
  - `build:debug --compilation_mode=dbg`
  - `test:debug --test_output=all`

### BUILD Files

**Library pattern** (`libs/*/BUILD.bazel`):
- `py_library` with `name = "<lib_name>"`, `srcs = glob(["**/*.py"])`, `visibility` scoped to `//apps:__subpackages__`
- External deps referenced as `@pip//<package_name>` (e.g., `@pip//pydantic`)

**Binary pattern** (`apps/*/BUILD.bazel`):
- `py_binary` with `name = "<app_name>"`, `srcs = ["main.py"]`, `main = "main.py"`, `deps` including internal libs and pip packages
- Add `py_test` in same BUILD file for app-specific integration tests

**Test targets** (`tests/BUILD.bazel`):
- `py_test` targets with `deps` pointing to the libraries under test and `@pip//pytest`
- `size = "small"` for unit tests, `size = "medium"` for integration tests
- Tags: `["unit"]` for unit tests, `["integration"]` for integration tests

### Custom Macro (`tools/BUILD.bazel`)

- Define macro `py_service(name, srcs, deps, port)` that creates:
  1. A `py_binary` target `<name>`
  2. A `py_test` target `<name>_test` that runs the app's test suite
  3. A `genrule` target `<name>_docker` that generates a Dockerfile for the service
- The macro should be loadable via `load("//tools:macros.bzl", "py_service")`
- Create `tools/macros.bzl` for the macro definition

### Expected Functionality

- `bazel build //...` successfully builds all targets (both apps and all libs)
- `bazel test //tests/...` runs all test targets
- `bazel build //apps/api` produces a runnable Flask API binary
- `bazel build //apps/pipeline` produces a runnable Click CLI binary
- `bazel query "deps(//apps/api)"` shows transitive dependencies including `//libs/core`, `//libs/models`, and `@pip//flask`
- `.bazelrc` with `--config=ci` enables remote caching for CI builds

## Acceptance Criteria

- `cd examples/python-bazel && bazel build //...` completes successfully with exit code 0
- All `py_library` targets have correctly scoped visibility (not public)
- `py_binary` targets correctly depend on internal libs and pip packages
- WORKSPACE correctly configures `rules_python` and `pip_parse`
- `.bazelrc` defines valid `ci` and `debug` configuration groups
- Test targets are properly sized and tagged
- `python -m pytest /workspace/tests/test_bazel_build_optimization.py -v --tb=short` passes
