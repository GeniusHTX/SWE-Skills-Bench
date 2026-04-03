# Task: Configure Turborepo Pipeline and Caching for the Cache Demo Workspace

## Background

The Turbo monorepo (https://github.com/vercel/turbo) contains an `examples/cache-demo` workspace that demonstrates Turborepo's caching capabilities. The current configuration needs to be extended to support a multi-package workspace with three packages — a shared UI component library, a documentation site, and a web application — each with build, test, and lint tasks that correctly declare dependencies, inputs, outputs, and cache behavior via `turbo.json`.

## Files to Create/Modify

- `examples/cache-demo/turbo.json` (modify) — Define pipeline tasks (`build`, `test`, `lint`, `dev`) with correct `dependsOn`, `inputs`, `outputs`, and `cache` settings for each task type
- `examples/cache-demo/packages/ui/package.json` (create) — Shared UI component library package with `build`, `test`, and `lint` scripts
- `examples/cache-demo/packages/ui/turbo.json` (create) — Package-level Turborepo configuration overriding the root for `ui`-specific build outputs (`dist/**`)
- `examples/cache-demo/packages/ui/src/index.ts` (create) — Entry point exporting shared UI components (Button, Card, Input)
- `examples/cache-demo/packages/ui/tsconfig.json` (create) — TypeScript configuration for the UI library
- `examples/cache-demo/apps/docs/package.json` (modify) — Documentation site that depends on `@cache-demo/ui`
- `examples/cache-demo/apps/web/package.json` (modify) — Web application that depends on `@cache-demo/ui`
- `examples/cache-demo/pnpm-workspace.yaml` (modify) — Ensure workspace includes `packages/*` and `apps/*`

## Requirements

### Pipeline Configuration (Root turbo.json)

- `build` task must depend on `^build` (topological dependencies) so that `@cache-demo/ui` builds before `apps/docs` and `apps/web`
- `build` must declare `outputs` as `["dist/**", ".next/**"]` to cache build artifacts
- `build` must declare `inputs` as `["src/**", "tsconfig.json", "package.json"]` to only invalidate cache when source files change
- `test` task must depend on `build` (same-package dependency) so tests run against built artifacts
- `test` must have `cache: false` if the workspace uses non-deterministic tests, or `cache: true` with `outputs: []` for deterministic tests
- `lint` task must have no `dependsOn` (can run in parallel with everything) and `cache: true` with `outputs: []`
- `dev` task must have `cache: false` and `persistent: true` since it runs a long-lived dev server

### Shared UI Package

- Package name must be `@cache-demo/ui` and version `0.0.0`
- Must export at least three components: `Button`, `Card`, and `Input`
- Must include a `build` script that compiles TypeScript to `dist/`
- Must include a `lint` script using the workspace's linter

### Dependency Graph

- `apps/web/package.json` must declare `@cache-demo/ui` as a workspace dependency using the `workspace:*` protocol
- `apps/docs/package.json` must declare `@cache-demo/ui` as a workspace dependency using the `workspace:*` protocol
- The root `pnpm-workspace.yaml` must include both `packages/*` and `apps/*` directories

### Cache Behavior

- Running `turbo run build` twice in succession must show cache hits (`FULL TURBO`) on the second run for all three packages if no source files changed
- Modifying a file in `packages/ui/src/` must invalidate the cache for `@cache-demo/ui` build and transitively for `apps/web` and `apps/docs` builds
- The `lint` task cache must be independent of the `build` task — changing build outputs must not invalidate lint cache

### Expected Functionality

- `npm install && npx turbo run build` from `examples/cache-demo/` completes successfully with all 3 packages built
- `npx turbo run build` again immediately prints `cache hit` for all tasks
- After editing `packages/ui/src/index.ts`, `npx turbo run build` shows cache miss for `@cache-demo/ui`, `apps/web`, and `apps/docs`
- `npx turbo run lint` runs in parallel across all packages without waiting for builds

## Acceptance Criteria

- `cd examples/cache-demo && npm install && npm run build` exits with code 0
- The `turbo.json` pipeline defines `build`, `test`, `lint`, and `dev` with correct `dependsOn`, `outputs`, `inputs`, `cache`, and `persistent` settings
- `@cache-demo/ui` is a valid workspace package exporting `Button`, `Card`, and `Input` components
- Topological build order is enforced: `@cache-demo/ui` builds before both apps
- Repeated builds without source changes produce cache hits for all tasks
- Source file changes correctly invalidate downstream caches through the dependency graph
