# Task: Create Bazel Remote Execution Example Project

## Background
   Add a minimal but complete Bazel
   project example demonstrating remote execution configuration and
   build caching patterns to the Bazel repository.

## Files to Create/Modify
   - examples/python-bazel/WORKSPACE (workspace configuration)
   - examples/python-bazel/BUILD.bazel (root build file)
   - examples/python-bazel/.bazelrc (build configuration)
   - examples/python-bazel/src/BUILD.bazel (source build)
   - examples/python-bazel/src/main.py (sample Python code)
   - examples/python-bazel/tests/BUILD.bazel (test build)

## Requirements
   
   Project Structure:
   - Simple py_binary target in src/
   - py_test targets in tests/
   - Hermetic Python toolchain configuration
   
   .bazelrc Configuration:
   - Remote cache configuration (commented placeholder)
   - Remote execution flags (commented placeholder)
   - Local development settings
   - CI-specific settings
   
   Build Targets:
   - //src:main (Python binary)
   - //tests:all (test suite)
   - //:format (formatting target, optional)

4. Configuration Flags to Include:
   - --remote_cache placeholder
   - --remote_executor placeholder
   - --spawn_strategy options
   - --disk_cache for local caching

## Acceptance Criteria
   - `cd examples/python-bazel && bazel build //...` exits with code 0
   - `cd examples/python-bazel && bazel test //...` passes
   - .bazelrc contains documented remote execution configuration
