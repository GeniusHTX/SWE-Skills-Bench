# Task: Configure Bazel Build System for a Polyglot Monorepo with Remote Caching

## Background

A monorepo containing a TypeScript web application, a Python ML service, a Go API gateway, and shared protobuf definitions needs a Bazel build setup. The configuration must include a WORKSPACE file with external dependencies, BUILD files for each project, a `.bazelrc` with remote caching and CI presets, custom Starlark rules for protobuf code generation, and visibility/dependency enforcement across packages.

## Files to Create/Modify

- `WORKSPACE.bazel` (create) — Root workspace file: register toolchains for TypeScript, Python, Go, and Protobuf
- `.bazelrc` (create) — Build configurations: local development, remote caching, CI, sandboxing, performance tuning
- `.bazelversion` (create) — Pin Bazel version to 7.0.0
- `platforms/BUILD.bazel` (create) — Platform definitions for linux_x86_64 and macos_arm64
- `apps/web/BUILD.bazel` (create) — TypeScript web app: build, test, bundle, container image targets
- `services/ml/BUILD.bazel` (create) — Python ML service: py_binary, py_test, py_image targets
- `services/gateway/BUILD.bazel` (create) — Go API gateway: go_binary, go_test, go_image targets
- `proto/BUILD.bazel` (create) — Protobuf definitions: proto_library, go_proto_library, python_proto_library
- `tools/rules/proto_gen.bzl` (create) — Custom Starlark rule for multi-language protobuf generation
- `tools/rules/docker.bzl` (create) — Custom Starlark macro wrapping container_image with standard labels and health check
- `tools/lint/BUILD.bazel` (create) — Lint targets: buildifier for BUILD files, ESLint for TypeScript, pylint for Python
- `.github/workflows/bazel-ci.yml` (create) — GitHub Actions workflow using Bazel with remote cache

## Requirements

### WORKSPACE (`WORKSPACE.bazel`)

```python
workspace(name = "monorepo")
```

Register toolchains:

**TypeScript (aspect_rules_js v1.34.0):**
- `http_archive` for `aspect_rules_js`.
- `rules_js_dependencies()`, `nodejs_register_toolchains(node_version = "20.11.0")`.
- `npm_translate_lock(pnpm_lock = "//:pnpm-lock.yaml")`.

**Python (rules_python v0.27.0):**
- `http_archive` for `rules_python`.
- `python_register_toolchains(python_version = "3.12")`.
- `pip_parse(name = "pip", requirements_lock = "//services/ml:requirements_lock.txt")`.

**Go (rules_go v0.44.0):**
- `http_archive` for `rules_go` and `gazelle`.
- `go_register_toolchains(version = "1.22.0")`.
- `go_rules_dependencies()`, `go_repository` deps via gazelle.

**Protobuf:**
- `rules_proto` and language-specific proto rules.
- `grpc` dependencies for Go and Python.

**Container rules (rules_oci v1.5.0):**
- `http_archive` for `rules_oci`.
- `oci_register_toolchains()`.
- Base images: `oci_pull` for `gcr.io/distroless/cc-debian12` (Go), `gcr.io/distroless/python3-debian12` (Python), `gcr.io/distroless/nodejs20-debian12` (TypeScript).

### .bazelrc Configuration

```bash
# Common
common --enable_bzlmod=false
build --incompatible_enable_cc_toolchain_resolution
build --experimental_strict_conflict_checks

# Performance
build --jobs=auto
build --local_cpu_resources=HOST_CPUS*.75
build --local_ram_resources=HOST_RAM*.75
build --worker_max_instances=4

# Caching
build --disk_cache=~/.cache/bazel-disk
build --repository_cache=~/.cache/bazel-repo

# Remote cache
build:remote-cache --remote_cache=grpcs://cache.buildbuddy.io
build:remote-cache --remote_upload_local_results=true
build:remote-cache --remote_timeout=3600
build:remote-cache --remote_header=x-buildbuddy-api-key=PLACEHOLDER

# Remote execution
build:remote-exec --remote_executor=grpcs://remote.buildbuddy.io
build:remote-exec --remote_instance_name=monorepo/default
build:remote-exec --jobs=200
build:remote-exec --remote_default_exec_properties=OSFamily=Linux
build:remote-exec --remote_default_exec_properties=container-image=docker://gcr.io/bazel-public/ubuntu2204-java17@sha256:...

# CI preset
build:ci --config=remote-cache
build:ci --build_metadata=ROLE=CI
build:ci --noshow_progress
build:ci --curses=no
build:ci --color=yes
build:ci --bes_results_url=https://app.buildbuddy.io/invocation/
build:ci --bes_backend=grpcs://remote.buildbuddy.io

# Test
test --test_output=errors
test --test_summary=detailed
test --flaky_test_attempts=2

# Platforms
build:linux --platforms=//platforms:linux_x86_64
build:macos --platforms=//platforms:macos_arm64

# Sandboxing
build --sandbox_default_allow_network=false
build --incompatible_strict_action_env

# Import user overrides
try-import %workspace%/user.bazelrc
```

### TypeScript Web App (`apps/web/BUILD.bazel`)

```python
load("@aspect_rules_js//js:defs.bzl", "js_library", "js_test")
load("@aspect_rules_js//js:defs.bzl", "js_binary")
load("@npm//:defs.bzl", "npm_link_all_packages")

npm_link_all_packages(name = "node_modules")

js_library(
    name = "web_lib",
    srcs = glob(["src/**/*.ts", "src/**/*.tsx"]),
    deps = [
        ":node_modules",
        "//proto:user_ts_proto",
        "//proto:order_ts_proto",
    ],
    visibility = ["//apps:__subpackages__"],
)

js_test(
    name = "web_test",
    srcs = glob(["src/**/*.test.ts"]),
    deps = [":web_lib", ":node_modules"],
)

js_binary(
    name = "web_bundle",
    entry_point = "src/main.ts",
    deps = [":web_lib"],
)
```

Include `oci_image` target producing container from distroless/nodejs20.

### Python ML Service (`services/ml/BUILD.bazel`)

```python
load("@rules_python//python:defs.bzl", "py_binary", "py_library", "py_test")
load("@pip//:requirements.bzl", "requirement")

py_library(
    name = "ml_lib",
    srcs = glob(["src/**/*.py"]),
    deps = [
        requirement("fastapi"),
        requirement("numpy"),
        requirement("scikit-learn"),
        requirement("pydantic"),
        "//proto:prediction_py_proto",
    ],
    visibility = ["//services:__subpackages__"],
)

py_binary(
    name = "ml_service",
    srcs = ["src/main.py"],
    main = "src/main.py",
    deps = [":ml_lib"],
)

py_test(
    name = "ml_test",
    srcs = glob(["tests/**/*.py"]),
    deps = [":ml_lib", requirement("pytest")],
    size = "medium",
    timeout = "short",
)
```

### Go API Gateway (`services/gateway/BUILD.bazel`)

```python
load("@io_bazel_rules_go//go:def.bzl", "go_binary", "go_library", "go_test")

go_library(
    name = "gateway_lib",
    srcs = glob(["*.go"], exclude = ["*_test.go"]),
    importpath = "github.com/myorg/monorepo/services/gateway",
    deps = [
        "//proto:user_go_proto",
        "//proto:order_go_proto",
        "@org_golang_google_grpc//:grpc",
        "@com_github_gin_gonic_gin//:gin",
    ],
    visibility = ["//services:__subpackages__"],
)

go_binary(
    name = "gateway",
    embed = [":gateway_lib"],
)

go_test(
    name = "gateway_test",
    srcs = glob(["*_test.go"]),
    embed = [":gateway_lib"],
    size = "small",
)
```

### Protobuf (`proto/BUILD.bazel`)

Define proto_library targets for `user.proto`, `order.proto`, `prediction.proto`. Each generates Go, Python, and TypeScript bindings:

```python
load("@rules_proto//proto:defs.bzl", "proto_library")
load("//tools/rules:proto_gen.bzl", "multi_lang_proto_library")

proto_library(
    name = "user_proto",
    srcs = ["user.proto"],
    visibility = ["//visibility:public"],
)

multi_lang_proto_library(
    name = "user",
    proto = ":user_proto",
    languages = ["go", "python", "typescript"],
)
```

### Custom Starlark Rule (`tools/rules/proto_gen.bzl`)

`multi_lang_proto_library` macro:
- Takes `name`, `proto` (label), `languages` (list of strings).
- For each language in languages:
  - `"go"` → generates `{name}_go_proto` target using `go_proto_library`.
  - `"python"` → generates `{name}_py_proto` target using `py_proto_library`.
  - `"typescript"` → generates `{name}_ts_proto` target using custom `ts_proto_library` rule (runs `protoc-gen-ts`).
- All generated targets have `visibility = ["//visibility:public"]`.

### Docker Macro (`tools/rules/docker.bzl`)

`service_container` macro:
- Takes `name`, `binary` (label), `base_image`, `port`.
- Creates `oci_image` with standard labels: `org.opencontainers.image.source`, `org.opencontainers.image.version` (from `--stamp`), `org.opencontainers.image.created`.
- Adds healthcheck: `CMD ["wget", "--spider", "http://localhost:{port}/health"]`.
- Creates `oci_tarball` for local loading and `oci_push` for registry.

### GitHub Actions CI (`.github/workflows/bazel-ci.yml`)

- Trigger: push to main, pull requests.
- Jobs:
  - `build-and-test`:
    - `ubuntu-latest`, checkout, install Bazelisk.
    - `bazel build --config=ci //...`.
    - `bazel test --config=ci //...`.
    - Upload test logs as artifact.
  - `affected-targets` (PR only):
    - Run `bazel query 'rdeps(//..., set($(git diff --name-only origin/main)))' ` to find affected targets.
    - Only build/test affected targets for faster PR checks.

### Expected Functionality

- `bazel build //...` → builds all targets: TypeScript web app, Python ML service, Go gateway, protobuf bindings.
- `bazel test //...` → runs all tests in hermetic sandbox.
- `bazel build --config=remote-cache //...` → uses BuildBuddy remote cache for incremental builds.
- `bazel build //services/gateway:gateway` → only rebuilds Go gateway if its sources or proto deps changed.
- Changing `proto/user.proto` → rebuilds Go, Python, and TypeScript proto bindings and all dependents.
- `bazel build //apps/web:web_image` → produces distroless container image.

## Acceptance Criteria

- WORKSPACE registers toolchains for TypeScript (Node 20), Python (3.12), Go (1.22), and Protobuf with gRPC.
- Container base images use distroless variants for each language runtime.
- `.bazelrc` configures local performance (CPU/RAM limits, sandbox), disk cache, remote cache, remote execution, CI preset, and platform selection.
- Sandboxing disables network access (`sandbox_default_allow_network=false`) for hermetic builds.
- BUILD files define library, binary, test, and container image targets for each service.
- Visibility rules restrict package access: service libs visible to `//services:__subpackages__`, protos to `//visibility:public`.
- `multi_lang_proto_library` macro generates Go, Python, and TypeScript proto targets from a single proto_library.
- `service_container` macro produces OCI images with standard labels and health checks.
- GitHub Actions workflow uses `--config=ci` with remote cache and an affected-targets job for PR optimization.
- `.bazelversion` pins Bazel to 7.0.0 for reproducibility.
