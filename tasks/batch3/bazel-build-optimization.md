# Task: Create a Multi-Language Bazel Build Configuration with Remote Caching

## Background

Bazel (https://github.com/bazelbuild/bazel) is a build and test tool that supports multi-language projects. The project needs a complete Bazel build configuration for a Python application example that includes: WORKSPACE setup with external dependencies, BUILD files with proper targets, `.bazelrc` with performance optimizations, and a custom Starlark rule for code generation.

## Files to Create/Modify

- `examples/python-bazel/WORKSPACE` (create) — Workspace file with Python toolchain and external dependency declarations
- `examples/python-bazel/BUILD` (create) — Root BUILD file with Python binary, library, and test targets
- `examples/python-bazel/.bazelrc` (create) — Bazel configuration with remote caching, sandboxing, and performance options
- `examples/python-bazel/src/BUILD` (create) — BUILD file for source library targets
- `examples/python-bazel/src/app.py` (create) — Main application entry point
- `examples/python-bazel/src/utils/BUILD` (create) — BUILD file for utility library
- `examples/python-bazel/src/utils/helpers.py` (create) — Utility functions
- `examples/python-bazel/tests/BUILD` (create) — BUILD file for test targets
- `examples/python-bazel/tests/test_app.py` (create) — Tests for the application
- `examples/python-bazel/rules/codegen.bzl` (create) — Custom Starlark rule for generating Python code from templates

## Requirements

### WORKSPACE Configuration

- Load `rules_python` for Python toolchain setup
- Register a Python 3.11 toolchain using `python_register_toolchains`
- Define external dependencies using `pip_parse` or `pip_install` for: `requests>=2.28.0`, `pydantic>=2.0.0`, `pytest>=7.0.0`
- Each external dependency must be pinnable to an exact version via a `requirements_lock.txt` file

### BUILD Files Structure

- Root BUILD: define a `py_binary` target `app` depending on `//src:lib`
- `src/BUILD`: define a `py_library` target `lib` with `srcs = ["app.py"]` depending on `//src/utils:helpers` and external `requests` and `pydantic` packages
- `src/utils/BUILD`: define a `py_library` target `helpers` with `srcs = ["helpers.py"]`
- `tests/BUILD`: define a `py_test` target `test_app` depending on `//src:lib` and external `pytest` package
- Set appropriate `visibility` on all targets: libraries are visible within the project, the binary is public
- Add `tags = ["manual"]` to any targets that should not run in `bazel test //...`

### .bazelrc Configuration

- Enable remote caching: `build --remote_cache=grpc://localhost:9092` (configurable)
- Enable build without the bytes: `build --remote_download_outputs=minimal`
- Set sandbox options: `build --sandbox_default_allow_network=false`
- Set performance options: `build --jobs=auto`, `build --experimental_ui_max_stdouterr_bytes=1048576`
- Set Python-specific options: `build --python_path=python3`
- Define configurations: `build:ci --remote_cache=grpc://cache.ci.example.com:443`, `build:ci --google_default_credentials`
- Enable test output streaming: `test --test_output=errors`
- Set memory optimization: `startup --host_jvm_args=-Xmx4g`

### Custom Starlark Rule

- Implement a `codegen_rule` in `rules/codegen.bzl` that:
  - Takes a `template` file (`.py.tmpl`) and a `config` file (JSON with variable definitions)
  - Generates a Python source file by replacing `{{variable}}` placeholders in the template with values from config
  - Declares the generated file as an output that other `py_library` targets can depend on
  - The rule implementation uses `ctx.actions.run` with a generator script
- Include a generator script that reads the template and config, performs substitution, and writes the output

### Application Code

- `src/app.py`: a simple HTTP client using `requests` that fetches data from a configurable URL and validates the response using a `pydantic` model
- `src/utils/helpers.py`: utility functions for URL validation and response parsing
- `tests/test_app.py`: pytest tests for the application logic (mock HTTP calls)

### Expected Functionality

- `bazel build //...` builds all targets successfully
- `bazel test //tests:test_app` runs the pytest tests
- `bazel run //:app` runs the application
- `bazel build //... --config=ci` uses the CI-specific remote cache configuration
- The custom codegen rule generates a valid Python file from a template and config
- Dependencies are properly resolved from the lockfile

## Acceptance Criteria

- WORKSPACE loads `rules_python`, registers Python 3.11 toolchain, and pins external dependencies
- BUILD files define correct `py_binary`, `py_library`, and `py_test` targets with proper dependencies and visibility
- `.bazelrc` configures remote caching, sandbox, performance options, and CI-specific overrides
- The custom Starlark rule generates Python code from templates with variable substitution
- `bazel build //...` completes successfully with exit code 0
- `bazel test //...` runs tests successfully
- Dependency graph is correct: binary → library → utils, tests → library
- All targets have appropriate visibility settings
