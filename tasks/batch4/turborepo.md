# Task: Configure Turborepo Build Pipeline for a Cache-Demo Monorepo

## Background

The Turbo repository (https://github.com/vercel/turbo) includes an `examples/cache-demo` monorepo that contains multiple packages and applications. This example needs a properly configured Turborepo pipeline with task dependencies, caching rules, environment variable handling, and CI-optimized settings so that builds, tests, and linting run correctly with proper parallelization and cache behavior.

## Files to Create/Modify

- `examples/cache-demo/turbo.json` (create or modify) — Root Turborepo configuration defining task pipeline, cache outputs, and environment variable dependencies
- `examples/cache-demo/apps/web/package.json` (modify) — Add build, lint, and test scripts for the web application
- `examples/cache-demo/apps/api/package.json` (modify) — Add build, lint, and test scripts for the API application
- `examples/cache-demo/packages/ui/package.json` (modify) — Add build and lint scripts for the shared UI package
- `examples/cache-demo/packages/utils/package.json` (create) — New shared utility package with build and test scripts
- `examples/cache-demo/packages/utils/src/index.ts` (create) — Utility functions exported by the new package
- `examples/cache-demo/package.json` (modify) — Root package.json with Turbo-delegating scripts

## Requirements

### Task Pipeline Configuration

- `build` task must declare `dependsOn: ["^build"]` so that package builds run after their dependencies
- `build` outputs must include `dist/**` and `.next/**` so Turborepo caches the correct artifacts
- `lint` task must have no dependencies and no outputs (it is a pure check with no cacheable artifacts)
- `test` task must declare `dependsOn: ["build"]` so tests run after the current package's build succeeds
- `dev` task must be marked as `persistent: true` and `cache: false` since it runs a long-lived dev server

### Package Scripts

- Each application and package must define its own `build`, `lint`, and `test` scripts in its `package.json`
- The root `package.json` must delegate to Turborepo via `turbo run <task>` — no direct build commands in the root scripts
- The `web` app build script must run `next build`; the `api` app build script must run `tsc`; the `ui` and `utils` packages must run `tsc` for build

### Shared Utility Package

- Create a `packages/utils` package that exports at least three utility functions: `formatCurrency(amount: number, currency?: string): string`, `slugify(text: string): string`, and `clamp(value: number, min: number, max: number): number`
- The `packages/utils/package.json` must declare the package name, main entry point, and appropriate dependencies
- The `web` and `api` apps must declare `packages/utils` as a workspace dependency

### Environment Variable Handling

- `turbo.json` must declare environment variable dependencies so that changes to specified env vars invalidate the cache
- The `build` task must include `NODE_ENV` and any `NEXT_PUBLIC_*` variables in its environment key
- The `test` task must include `CI` and `DATABASE_URL` in its environment key

### Cache Behavior

- Running `turbo run build` twice without changes must hit cache on the second run (exit instantly with `>>> FULL TURBO` indicators)
- Changing a source file in `packages/utils` must cause `packages/utils` build to miss cache, and any dependent package build must also miss cache
- Changing an environment variable listed in the `env` key must cause a cache miss for the affected task

### Expected Functionality

- `npm install && npm run build` from `examples/cache-demo` root completes successfully, building all packages and apps in correct dependency order
- `npm run lint` runs linting across all packages in parallel
- `npm run test` runs tests after builds complete
- Modifying `packages/utils/src/index.ts` and re-running `npm run build` rebuilds only `utils`, `web`, and `api` (the dependents), not `ui`
- Running `npm run build` a second time with no changes shows all tasks cached

## Acceptance Criteria

- `npm install && npm run build` in `examples/cache-demo` exits with code 0, producing build artifacts for all packages and apps
- `turbo.json` defines `build`, `lint`, `test`, and `dev` tasks with correct `dependsOn`, `outputs`, and `env` configurations
- Each package and app has its own build/lint/test scripts; the root `package.json` uses only `turbo run` delegation
- The `packages/utils` package exists with the three specified utility functions and is consumed by `web` and `api`
- A second `turbo run build` with no changes reports cache hits for all tasks
- Modifying a source file in a dependency correctly invalidates the cache for that package and its dependents
