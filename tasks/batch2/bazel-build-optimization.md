# Task: Create a Python Bazel Build Example

## Background

Bazel (https://github.com/bazelbuild/bazel) is a build system for large-scale software. A new example project is needed under `examples/python-bazel/` demonstrating how to build, test, and package a Python application with Bazel, including library targets, binary targets, and test targets.

## Files to Create

- Files under `examples/python-bazel/` including:
  - `BUILD` or `BUILD.bazel` files defining Python library, binary, and test targets
  - `WORKSPACE.bazel` or `MODULE.bazel` with rules_python configuration
  - Python source files for the library and binary
  - Python test files exercising the library

## Requirements

### Build Targets

- Define a `py_library` target for a reusable Python module
- Define a `py_binary` target for an executable script that depends on the library
- Define a `py_test` target that tests the library functions

### Workspace Configuration

- Configure the Python toolchain via rules_python
- Pin a specific Python interpreter version
- Declare any third-party dependencies via pip requirements

### Build Verification

- `bazel build //...` from the example directory must succeed
- `bazel test //...` from the example directory must pass

## Expected Functionality

- The library module provides functions importable by the binary and test targets
- The binary target runs successfully and exercises library functionality
- The test target validates library behavior and passes

## Acceptance Criteria

- The example defines a working Bazel-based Python project with a reusable library, an executable binary, and automated tests.
- The binary target imports and uses functionality from the library target rather than duplicating logic.
- The test target exercises the library's behavior and passes for representative inputs.
- Python toolchain and dependency configuration are declared explicitly in the example workspace setup.
- The example is structured so a user can understand how to build, run, and test a Python project with Bazel.
