# Task: Implement Bazel Build Configuration Generator with Remote Cache Validation and Dependency Analysis

## Background

The Bazel build system (`bazelbuild/bazel`) examples directory needs a Python project scaffold under `examples/python-bazel/` that demonstrates production-grade Bazel configuration including a WORKSPACE file with external dependencies, `.bazelrc` with remote cache settings, BUILD files for a multi-package Python library, and a dependency analysis utility. The implementation must produce a buildable project with `py_library`, `py_test`, and `py_binary` rules, and include a build configuration validator that checks `.bazelrc` and `WORKSPACE` files for correctness.

## Files to Create/Modify

- `examples/python-bazel/WORKSPACE.bazel` — Workspace configuration with rules_python, pip dependencies, and toolchain registration (new)
- `examples/python-bazel/.bazelrc` — Build configuration with performance flags, remote cache settings, CI profile, and test settings (new)
- `examples/python-bazel/BUILD.bazel` — Root BUILD file with package group visibility (new)
- `examples/python-bazel/src/lib/BUILD.bazel` — BUILD file for the core Python library with `py_library` rule (new)
- `examples/python-bazel/src/lib/__init__.py` — Package init (new)
- `examples/python-bazel/src/lib/graph.py` — Dependency graph module with topological sort and cycle detection (new)
- `examples/python-bazel/src/lib/config_validator.py` — Bazel config validator for `.bazelrc` and `WORKSPACE` files (new)
- `examples/python-bazel/src/bin/BUILD.bazel` — BUILD file for the CLI binary with `py_binary` rule (new)
- `examples/python-bazel/src/bin/analyzer.py` — CLI entry point that runs dependency analysis (new)
- `examples/python-bazel/tests/BUILD.bazel` — BUILD file with `py_test` rules (new)
- `examples/python-bazel/tests/__init__.py` — Test package init (new)
- `examples/python-bazel/tests/test_graph.py` — Unit tests for the dependency graph module (new)
- `examples/python-bazel/tests/test_config_validator.py` — Unit tests for the config validator (new)
- `examples/python-bazel/requirements.txt` — pip requirements for the project (new)

## Requirements

### WORKSPACE Configuration

- Workspace named `python_bazel_example`
- Load `rules_python` via `http_archive` with a pinned version and SHA-256 hash
- Register a Python toolchain for Python 3.11 via `python_register_toolchains`
- Configure `pip_parse` to install dependencies from `requirements.txt` with the registered Python interpreter
- Load `pip_repositories` from the generated pip lock

### .bazelrc Configuration

- `build --jobs=auto` and `build --local_cpu_resources=HOST_CPUS*.75`
- `build --disk_cache=~/.cache/bazel-disk` and `build --repository_cache=~/.cache/bazel-repo`
- `build:remote-cache --remote_cache=grpcs://cache.example.com` with `--remote_upload_local_results=true` and `--remote_timeout=3600`
- `build:ci --config=remote-cache` with `--build_metadata=ROLE=CI`
- `test --test_output=errors` and `test --test_summary=detailed`
- `try-import %workspace%/user.bazelrc` at the end

### BUILD Files

- Root `BUILD.bazel` defines `package_group(name = "internal", packages = ["//src/..."])` and sets default visibility
- `src/lib/BUILD.bazel` defines `py_library(name = "lib", srcs = glob(["*.py"]), visibility = ["//visibility:public"])` with deps on pip packages
- `src/bin/BUILD.bazel` defines `py_binary(name = "analyzer", srcs = ["analyzer.py"], deps = ["//src/lib"])` 
- `tests/BUILD.bazel` defines `py_test` targets for each test file, each depending on `//src/lib` and `requirement("pytest")`

### Dependency Graph Module (`graph.py`)

- `DependencyGraph` class with `add_target(label: str, deps: list[str])` where label follows Bazel format `//path/to:target`
- `resolve_order()` returns a list of labels in valid build order (topological sort); raises `CyclicDependencyError` with the cycle path if cycles exist
- `query_deps(label: str)` returns the transitive closure of all dependencies for a target
- `query_rdeps(label: str)` returns all targets that transitively depend on the given target
- `affected_targets(changed_files: list[str])` maps file paths to owning packages and returns all targets whose package or transitive deps include a changed file
- Validate that labels match the pattern `//[a-zA-Z0-9_/.-]+:[a-zA-Z0-9_.-]+` and raise `InvalidLabelError` for malformed labels

### Config Validator (`config_validator.py`)

- `validate_bazelrc(content: str)` returns a list of `ConfigIssue(line: int, severity: str, message: str)`:
  - Error if `--jobs` is set to a fixed number > 128 (should use `auto`)
  - Warning if `--disk_cache` is missing
  - Warning if `--repository_cache` is missing
  - Error if `--remote_cache` URL uses `http://` instead of `grpcs://` (insecure)
  - Warning if `try-import %workspace%/user.bazelrc` is absent
- `validate_workspace(content: str)` returns a list of `ConfigIssue`:
  - Error if `workspace(name = ...)` is missing
  - Error if any `http_archive` lacks a `sha256` attribute
  - Warning if no `python_register_toolchains` call is present
  - Error if `http_archive` URL uses `http://` instead of `https://`

### Expected Functionality

- `DependencyGraph` with `//src/lib:lib` → `//external:numpy`, `//src/bin:analyzer` → `//src/lib:lib` → `resolve_order()` returns `["//external:numpy", "//src/lib:lib", "//src/bin:analyzer"]`
- `DependencyGraph` with `//a:a` → `//b:b` → `//a:a` → `resolve_order()` raises `CyclicDependencyError` containing `//a:a` and `//b:b`
- `query_deps("//src/bin:analyzer")` returns `{"//src/lib:lib", "//external:numpy"}`
- `query_rdeps("//src/lib:lib")` returns `{"//src/bin:analyzer"}`
- `add_target("invalid label", [])` raises `InvalidLabelError`
- `validate_bazelrc` on content with `--remote_cache=http://cache.example.com` → returns error about insecure remote cache
- `validate_bazelrc` on content without `--disk_cache` → returns warning
- `validate_workspace` on content with `http_archive(name="rules_python", url="https://...", strip_prefix="...")` (missing sha256) → returns error
- `validate_workspace` on content without `workspace(name = ...)` → returns error
- `bazel build //...` from `examples/python-bazel/` succeeds
- `bazel test //tests/...` runs and passes both test files

## Acceptance Criteria

- `bazel build //...` in `examples/python-bazel/` exits with code 0
- `bazel test //tests:test_graph` passes all graph tests
- `bazel test //tests:test_config_validator` passes all config validator tests
- `WORKSPACE.bazel` loads `rules_python` with a pinned SHA-256 hash
- `.bazelrc` contains remote cache, CI config, and performance settings
- Topological sort produces valid build order and detects cycles with descriptive errors
- Transitive dependency queries (`query_deps`, `query_rdeps`) return complete closures
- Label validation rejects malformed Bazel labels
- Config validator catches insecure URLs, missing hashes, and absent required directives
- BUILD files use correct `py_library`, `py_test`, and `py_binary` rules with appropriate visibility and deps
- No hardcoded file paths in test assertions — all tests construct their own fixtures
