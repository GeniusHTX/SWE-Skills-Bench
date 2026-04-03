# Task: Build a Bazel Build Configuration Optimizer for a Python Monorepo

## Background

Bazel (https://github.com/bazelbuild/bazel) is a build system for large-scale monorepos. The project needs a Python tool that analyzes Bazel build configurations, identifies optimization opportunities, generates optimized BUILD files for Python projects, configures remote caching, and benchmarks build performance. The tool works on a sample Python monorepo structure within Bazel's examples directory.

## Files to Create/Modify

- `examples/python-bazel/tools/build_analyzer.py` (create) — `BuildAnalyzer` class that parses BUILD.bazel files, builds a dependency graph, identifies circular dependencies, detects overly broad dependency declarations, and reports build target statistics
- `examples/python-bazel/tools/build_generator.py` (create) — `BuildFileGenerator` class that generates optimized BUILD.bazel files for Python packages: `py_library`, `py_binary`, `py_test` targets with automatic dependency inference from imports, proper visibility declarations, and test size tags
- `examples/python-bazel/tools/cache_config.py` (create) — `RemoteCacheConfig` class generating `.bazelrc` configurations for remote caching (disk cache, HTTP cache, gRPC cache) with proper authentication, cache key composition, and platform-specific settings
- `examples/python-bazel/tools/build_benchmark.py` (create) — `BuildBenchmark` class measuring clean build time, incremental build time, test execution time, and cache hit rates across different configurations
- `examples/python-bazel/BUILD.bazel` (create) — BUILD file for the tools package itself with correct `py_library` and `py_test` targets
- `tests/test_bazel_build_optimization.py` (create) — Tests for build analysis, file generation, cache configuration, and benchmark measurement

## Requirements

### BuildAnalyzer

- Constructor: `BuildAnalyzer(workspace_root: str)`
- `parse_build_file(path: str) -> list[dict]`:
  - Parse BUILD.bazel file and extract targets: `{"name": str, "rule": str, "srcs": list[str], "deps": list[str], "visibility": list[str], "tags": list[str]}`
  - Support rules: `py_library`, `py_binary`, `py_test`, `py_proto_library`
  - Handle `glob()` patterns in `srcs` by resolving them against the filesystem
- `build_dependency_graph() -> dict[str, list[str]]`:
  - Adjacency list mapping target labels (`//pkg:target`) to their dependency labels
  - Resolve relative deps (`:target`) to absolute labels (`//pkg:target`)
- `find_circular_deps() -> list[list[str]]`:
  - Detect cycles in the dependency graph using DFS; return list of cycles (each cycle as a list of target labels)
- `find_unused_deps(target: str) -> list[str]`:
  - Compare declared `deps` against actual imports in `srcs` files
  - Return deps declared but never imported
- `target_statistics() -> dict`:
  - `total_targets`: int
  - `by_rule`: dict mapping rule name to count
  - `avg_deps`: float (average dependency count per target)
  - `max_deps_target`: str (target with most dependencies)
  - `targets_without_visibility`: list[str]

### BuildFileGenerator

- Constructor: `BuildFileGenerator(package_path: str)`
- `infer_targets() -> list[dict]`:
  - Scan `.py` files in the package
  - `__init__.py` files indicate a `py_library`
  - Files matching `*_test.py` or `test_*.py` are `py_test` targets
  - Files with `if __name__ == "__main__"` are `py_binary` targets
  - Remaining files are `py_library` srcs
- `infer_deps(source_file: str) -> list[str]`:
  - Parse Python imports from the file
  - Map `from pkg.module import X` to `//pkg:module` labels
  - External imports (not in workspace) are mapped to third-party labels: `@pip//package_name`
  - Return sorted, deduplicated list of labels
- `generate(visibility: list[str] = None) -> str`:
  - Produce valid BUILD.bazel content with proper `load()` statements
  - Default visibility: `["//visibility:private"]`
  - Add `size = "small"` tag to test targets by default
  - Sort targets alphabetically by name
- `optimize(existing_build: str) -> str`:
  - Parse existing BUILD file, compare with inferred targets, add missing deps, remove unused deps
  - Return the optimized BUILD content

### RemoteCacheConfig

- Constructor: `RemoteCacheConfig(cache_type: str)` where `cache_type` is `"disk"`, `"http"`, or `"grpc"`
- `generate_bazelrc() -> str`:
  - `"disk"`: `build --disk_cache=/path/to/cache`
  - `"http"`: `build --remote_cache=http://cache-server:8080` with `--remote_upload_local_results`
  - `"grpc"`: `build --remote_cache=grpc://cache-server:9092` with authentication flags
  - All types include: `--remote_timeout=60`, `build --jobs=auto`, `build --local_cpu_resources=HOST_CPUS*.75`
- `platform_config(os: str, arch: str) -> str`:
  - Generate platform execution properties for cache key differentiation
  - `platform(name = "remote_platform", exec_properties = {"OSFamily": os, "Arch": arch})`
- `cache_key_config(extra_keys: dict = None) -> str`:
  - Generate `--host_platform_remote_properties_override` flags
  - Include Python version and OS in cache key
- Invalid `cache_type`: raise `ValueError`

### BuildBenchmark

- Constructor: `BuildBenchmark(workspace_root: str, target: str = "//...")`
- `clean_build() -> dict`:
  - Run `bazel clean`, then `bazel build {target}`
  - Return `{"duration_s": float, "targets_built": int, "actions_executed": int}`
  - Parse Bazel output for action counts
- `incremental_build(modified_file: str) -> dict`:
  - Touch the specified file, re-run build
  - Return same metrics plus `cache_hits: int` and `cache_hit_rate: float`
- `test_run(test_target: str = "//...", runs: int = 1) -> dict`:
  - `bazel test {test_target}` with `--runs_per_test={runs}`
  - Return `{"duration_s": float, "tests_passed": int, "tests_failed": int, "tests_skipped": int}`
- `compare_configs(configs: list[dict]) -> list[dict]`:
  - Each config: `{"name": str, "bazelrc_content": str}`
  - Run clean build with each config and return comparative results
- `generate_report(results: dict) -> str` — Markdown-formatted benchmark report

### Edge Cases

- BUILD file with syntax errors: `parse_build_file` logs warning and returns partial results
- Python file with `try: import X except ImportError: import Y` pattern: infer deps for both X and Y
- Circular dependency of length 1 (self-dependency): detected and reported
- Workspace with no BUILD files: `build_dependency_graph()` returns empty graph
- `glob()` pattern matching no files: `srcs` is empty, log warning

## Expected Functionality

- `BuildAnalyzer` parses a workspace with 20 BUILD files, builds dependency graph, and finds 2 circular dependencies
- `BuildFileGenerator` scans a Python package with 10 files and generates a BUILD.bazel with correctly inferred targets and dependencies
- `RemoteCacheConfig("http").generate_bazelrc()` produces valid `.bazelrc` content for HTTP remote caching
- `BuildBenchmark.clean_build()` reports build duration, action count, and target count

## Acceptance Criteria

- `BuildAnalyzer` correctly parses BUILD.bazel files and builds dependency graphs with cycle detection
- `BuildFileGenerator` infers Python library, binary, and test targets with correct dependency labels
- `RemoteCacheConfig` generates valid `.bazelrc` content for disk, HTTP, and gRPC cache types
- `BuildBenchmark` measures clean and incremental build times with cache hit tracking
- Circular dependencies, unused deps, and missing visibility are detected and reported
- All tests pass with `pytest`
