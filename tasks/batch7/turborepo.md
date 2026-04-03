# Task: Add a Cache-Demo Application to the Turborepo Examples Directory

## Background

The Turborepo repository (https://github.com/vercel/turbo) provides a high-performance build system for JavaScript and TypeScript monorepos. The `examples/` directory contains starter projects demonstrating Turborepo features like caching, parallel execution, and dependency graph management. The task is to create a new `examples/cache-demo/` application that demonstrates Turborepo's task caching, input hashing, and cache invalidation through a multi-package workspace with concrete build, test, and lint tasks.

## Files to Create/Modify

- `examples/cache-demo/package.json` (create) — Root workspace package.json with Turborepo as a dev dependency and workspace definition
- `examples/cache-demo/turbo.json` (create) — Turborepo pipeline configuration defining build, test, and lint tasks with caching rules and dependency ordering
- `examples/cache-demo/packages/shared-utils/package.json` (create) — Shared utility library package manifest
- `examples/cache-demo/packages/shared-utils/src/index.ts` (create) — Utility functions (string formatting, date helpers) exported as a library
- `examples/cache-demo/packages/shared-utils/tsconfig.json` (create) — TypeScript configuration for the shared library
- `examples/cache-demo/apps/web/package.json` (create) — Web application package that depends on `shared-utils`
- `examples/cache-demo/apps/web/src/index.ts` (create) — Web app entry point importing from shared-utils
- `examples/cache-demo/apps/web/tsconfig.json` (create) — TypeScript configuration for the web app
- `examples/cache-demo/apps/api/package.json` (create) — API application package that depends on `shared-utils`
- `examples/cache-demo/apps/api/src/index.ts` (create) — API entry point importing from shared-utils
- `examples/cache-demo/apps/api/tsconfig.json` (create) — TypeScript configuration for the API app
- `examples/cache-demo/README.md` (create) — Documentation explaining the cache demo setup and how to observe caching behavior

## Requirements

### Workspace Structure

- The workspace must use npm workspaces with three packages: `packages/shared-utils`, `apps/web`, `apps/api`
- Both `apps/web` and `apps/api` must declare a dependency on `shared-utils` using workspace protocol (`"shared-utils": "*"`)
- Each package must have its own `build`, `test`, and `lint` scripts in its `package.json`

### Turborepo Pipeline Configuration (`turbo.json`)

- The `build` task must depend on `^build` (topological dependencies — shared-utils builds before apps)
- The `build` task must define `outputs` as `["dist/**"]` so build artifacts are cached
- The `test` task must depend on `build` (tests run only after build succeeds)
- The `test` task must have `cache: true` so test results are cached when inputs don't change
- The `lint` task must have no dependencies and `cache: true`
- Environment variables `NODE_ENV` and `API_URL` must be declared as `globalEnv` to be included in the cache hash

### Shared Utils Package

- Export at least three utility functions: `formatCurrency(amount: number, currency?: string): string`, `formatDate(date: Date, format?: string): string`, `slugify(text: string): string`
- The `build` script must compile TypeScript to the `dist/` directory
- The `test` script must run tests that verify each utility function
- The `lint` script must run a TypeScript type check (`tsc --noEmit`)

### Web and API Apps

- Each app must import and use at least one function from `shared-utils` in its entry point
- Each app's `build` script must compile TypeScript to `dist/`
- Each app must have at least one test file verifying its use of shared-utils
- Each app must have a `lint` script

### Caching Behavior

- Running `npx turbo build` twice without file changes must produce a full cache hit on the second run (all tasks show "FULL TURBO" or cached status)
- Modifying a file in `packages/shared-utils/src/` and running `npx turbo build` must rebuild shared-utils AND both apps (cache miss due to dependency change)
- Modifying a file in `apps/web/src/` must rebuild only `apps/web` (shared-utils and api remain cached)

## Expected Functionality

- `cd examples/cache-demo && npm install && npm run build` completes successfully, producing `dist/` directories in all three packages
- A second `npm run build` shows cache hits for all three packages
- Editing `packages/shared-utils/src/index.ts` and rebuilding triggers cache misses for all three packages
- `npm run test` runs tests in all packages successfully
- `npm run lint` runs type checks in all packages

## Acceptance Criteria

- The workspace contains three packages with correct dependency relationships (apps depend on shared-utils)
- `turbo.json` defines `build`, `test`, and `lint` tasks with correct dependency ordering, output declarations, and caching configuration
- `npm install && npm run build` succeeds in the `examples/cache-demo/` directory
- Repeated builds without source changes produce cached results
- Source changes in shared-utils invalidate caches for all dependent packages
- Source changes in an app invalidate only that app's cache
- All packages have passing tests and lint checks
