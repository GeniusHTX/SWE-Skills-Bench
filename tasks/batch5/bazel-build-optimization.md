# Task: Optimize Bazel Build Configuration for a Python Monorepo

## Background

Bazel (https://github.com/bazelbuild/bazel) is a build system supporting multi-language monorepos. This task requires creating an optimized Bazel build configuration for a Python monorepo with multiple packages: a shared library, a web service, a data pipeline, and a CLI tool. The configuration must leverage remote caching, test sharding, build transitions, and precise dependency management for fast incremental builds.

## Files to Create/Modify

- `examples/python-bazel/WORKSPACE` (create) — Workspace configuration: Python toolchain (`rules_python`), pip dependencies from `requirements_lock.txt`, and workspace-level repository rules.
- `examples/python-bazel/BUILD.bazel` (create) — Root BUILD file with visibility defaults and `config_setting` for build profiles (dev, ci, release).
- `examples/python-bazel/lib/BUILD.bazel` (create) — Shared library package: `py_library` targets with fine-grained deps, `py_test` targets with test sharding for the large test suite.
- `examples/python-bazel/lib/utils/BUILD.bazel` (create) — Utility sub-package with granular `py_library` targets (one per module) for minimal dependency fan-out.
- `examples/python-bazel/service/BUILD.bazel` (create) — Web service package: `py_binary` for the server, `py_image` for Docker (using `rules_docker`), health check test.
- `examples/python-bazel/pipeline/BUILD.bazel` (create) — Data pipeline package: `py_binary` for the pipeline runner, `py_test` with `size = "large"` and `timeout = "long"`, test data filegroup.
- `examples/python-bazel/cli/BUILD.bazel` (create) — CLI tool: `py_binary` with `entry_point`, using `args` for default flags.
- `examples/python-bazel/.bazelrc` (create) — Bazel configuration file with profiles: `--config=dev` (debug, no optimization), `--config=ci` (remote cache, test output), `--config=release` (optimized, stamped).
- `examples/python-bazel/requirements_lock.txt` (create) — Pinned pip dependencies for reproducible builds.
- `tests/test_bazel_build_optimization.py` (create) — Tests validating BUILD file structure, dependency correctness, and configuration settings.

## Requirements

### WORKSPACE

- Load `rules_python` from Bazel Central Registry or `http_archive`.
- Configure Python toolchain: `python_register_toolchains(name = "python3_11", python_version = "3.11")`.
- Load `pip_parse` for resolving requirements: `pip_parse(name = "pip", requirements_lock = "//:requirements_lock.txt")`.
- Use `load("@pip//:requirements.bzl", "requirement")` for pip dependency references.

### Shared Library (`lib/`)

- `py_library(name = "models", srcs = ["models.py"], deps = [requirement("pydantic")])`.
- `py_library(name = "database", srcs = ["database.py"], deps = [":models", requirement("sqlalchemy")])`.
- `py_library(name = "cache", srcs = ["cache.py"], deps = [requirement("redis")])`.
- Test target: `py_test(name = "models_test", srcs = ["models_test.py"], deps = [":models"], size = "small")`.
- Large test suite: `py_test(name = "database_test", srcs = ["database_test.py"], deps = [":database"], size = "medium", shard_count = 4)` — sharding splits test execution across 4 parallel workers.

### Utility Sub-Package (`lib/utils/`)

- One `py_library` per module: `py_library(name = "string_utils", srcs = ["string_utils.py"])`.
- `py_library(name = "date_utils", srcs = ["date_utils.py"], deps = [requirement("python-dateutil")])`.
- `py_library(name = "retry", srcs = ["retry.py"])`.
- This granularity ensures that changing `string_utils.py` does not invalidate caches for targets depending only on `date_utils`.

### Web Service (`service/`)

- `py_binary(name = "server", srcs = ["main.py"], deps = ["//lib:models", "//lib:database", "//lib:cache", requirement("fastapi"), requirement("uvicorn")])`.
- `py_test(name = "server_test", srcs = ["server_test.py"], deps = [":server", requirement("httpx")], tags = ["integration"])`.
- Visibility: `package(default_visibility = ["//visibility:private"])`, with `:server` having `visibility = ["//..."]`.

### Data Pipeline (`pipeline/`)

- `py_binary(name = "runner", srcs = ["runner.py"], deps = ["//lib:models", "//lib:database", requirement("pandas")])`.
- `filegroup(name = "test_data", srcs = glob(["testdata/**"]))`.
- `py_test(name = "runner_test", ..., data = [":test_data"], size = "large", timeout = "long")`.

### Bazel Configuration (`.bazelrc`)

```
# Common settings
build --incompatible_strict_action_env
build --enable_platform_specific_config

# Dev profile
build:dev --compilation_mode=dbg
build:dev --test_output=errors

# CI profile
build:ci --remote_cache=grpc://cache.example.com:9092
build:ci --test_output=all
build:ci --jobs=HOST_CPUS*0.75
build:ci --flaky_test_attempts=2

# Release profile
build:release --compilation_mode=opt
build:release --stamp
build:release --workspace_status_command=tools/workspace_status.sh
```

### Expected Functionality

- `bazel build //...` → builds all targets with correct dependency ordering.
- `bazel test //lib/...` → runs library tests with sharding (4 shards for database_test).
- Changing `lib/utils/string_utils.py` → only `string_utils` and its dependents rebuild; `date_utils` cache is preserved.
- `bazel build --config=ci //service:server` → builds with remote cache and optimized settings.
- `bazel test //pipeline:runner_test` → test has access to `testdata/` files.

## Acceptance Criteria

- WORKSPACE configures Python toolchain and pip dependencies correctly.
- Each BUILD file defines targets with precise, minimal dependencies.
- Test sharding is configured for the large test suite (`shard_count = 4`).
- Utility package has granular per-module `py_library` targets.
- `.bazelrc` defines 3 profiles (dev, ci, release) with appropriate settings.
- Remote cache is configured in the CI profile.
- `bazel build //...` succeeds on the example project.
- Tests validate BUILD file structure, dependency declarations, sharding config, and .bazelrc profiles.
