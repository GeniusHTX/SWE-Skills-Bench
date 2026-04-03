# Task: Configure an Nx Monorepo with Project Boundaries, Caching, and Affected Commands

## Background

The Nx repository (https://github.com/nrwl/nx) is a build system for monorepos. A new example workspace configuration is needed that demonstrates a properly structured Nx monorepo with two applications and three shared libraries, enforced project boundaries via tags and lint rules, optimized build caching, and CI pipeline using the affected command to only build/test changed projects.

## Files to Create/Modify

- `examples/nx-demo/nx.json` (create) — Root Nx configuration with task runner options, named inputs, target defaults, and generator defaults
- `examples/nx-demo/apps/web/project.json` (create) — Web application project configuration with tags and targets
- `examples/nx-demo/apps/api/project.json` (create) — API application project configuration
- `examples/nx-demo/libs/shared/ui/project.json` (create) — Shared UI library with boundary tags
- `examples/nx-demo/libs/shared/utils/project.json` (create) — Shared utils library with boundary tags
- `examples/nx-demo/libs/data-access/project.json` (create) — Data access library with boundary tags
- `examples/nx-demo/.eslintrc.json` (create) — ESLint configuration with `@nx/enforce-module-boundaries` rule
- `examples/nx-demo/tsconfig.base.json` (create) — Base TypeScript config with path mappings for all libraries
- `examples/nx-demo/.github/workflows/ci.yml` (create) — GitHub Actions CI workflow using `nx affected`
- `tests/test_nx_workspace_patterns.py` (create) — Python tests validating the configuration files

## Requirements

### nx.json Configuration

- `npmScope`: `"demo"`
- `affected.defaultBase`: `"main"`
- `tasksRunnerOptions.default`: runner `"nx/tasks-runners/default"` with `cacheableOperations` including `build`, `lint`, `test`, `e2e`; `parallel` set to 3
- `targetDefaults`:
  - `build`: `dependsOn: ["^build"]`, inputs: `["production", "^production"]`, cache: true
  - `test`: inputs: `["default", "^production", "{workspaceRoot}/jest.preset.js"]`, cache: true
  - `lint`: inputs: `["default", "{workspaceRoot}/.eslintrc.json"]`, cache: true
- `namedInputs`:
  - `default`: `["{projectRoot}/**/*", "sharedGlobals"]`
  - `production`: `["default", "!{projectRoot}/**/?(*.)+(spec|test).[jt]s?(x)?(.snap)", "!{projectRoot}/jest.config.[jt]s"]`
  - `sharedGlobals`: `["{workspaceRoot}/tsconfig.base.json"]`

### Project Configurations

- **apps/web**: `projectType: "application"`, tags: `["type:app", "scope:web"]`, targets: build (webpack executor), serve, test, lint
- **apps/api**: `projectType: "application"`, tags: `["type:app", "scope:api"]`, targets: build (node executor), serve, test, lint
- **libs/shared/ui**: `projectType: "library"`, tags: `["type:ui", "scope:shared"]`, targets: build, test, lint
- **libs/shared/utils**: `projectType: "library"`, tags: `["type:util", "scope:shared"]`, targets: build, test, lint
- **libs/data-access**: `projectType: "library"`, tags: `["type:data-access", "scope:shared"]`, targets: build, test, lint

### Module Boundary Rules

- ESLint `@nx/enforce-module-boundaries` rule with `depConstraints`:
  - `type:app` can depend on `type:ui`, `type:data-access`, `type:util`
  - `type:ui` can depend on `type:util` only
  - `type:data-access` can depend on `type:util` only
  - `type:util` cannot depend on any other type
- `allow` array must be empty (no exceptions)
- `enforceBuildableLibDependency` must be true

### TypeScript Path Mappings

- `@demo/shared/ui` → `libs/shared/ui/src/index.ts`
- `@demo/shared/utils` → `libs/shared/utils/src/index.ts`
- `@demo/data-access` → `libs/data-access/src/index.ts`

### CI Workflow

- Trigger on: push to `main`, pull request to `main`
- Steps: checkout, setup Node 20, install dependencies (`npm ci`), run `nx affected --target=lint --base=origin/main`, run `nx affected --target=test --base=origin/main`, run `nx affected --target=build --base=origin/main`
- Use `nrwl/nx-set-shas` action to determine correct base/head SHAs

### Expected Functionality

- Running `nx build web` first builds all library dependencies (`^build`), then builds the web app
- Running `nx affected --target=test` only tests projects affected by the current changes
- A UI library importing from a data-access library triggers an `enforce-module-boundaries` lint error
- Build caching means re-running `nx build web` without changes completes instantly from cache

## Acceptance Criteria

- `nx.json` has correct task runner, named inputs, target defaults, and generator configuration
- All project.json files have appropriate project types, tags, and target configurations
- ESLint module boundary rules enforce the dependency hierarchy (app → feature libs → util, no reverse)
- TypeScript base config has correct path mappings for all libraries
- CI workflow uses `nx affected` to run only changed project targets
- Tests validate JSON structure, tag assignments, boundary rules, and path mappings
