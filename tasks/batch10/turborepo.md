# Task: Add a Shared UI Package and Cache-Demo Pipeline to the Turbo Monorepo

## Background

The Turbo monorepo (https://github.com/vercel/turbo) contains an `examples/cache-demo` workspace that demonstrates Turborepo's caching behavior. This task adds a new shared `packages/ui` library to the cache-demo example and wires it into the existing apps, with a properly configured `turbo.json` pipeline for `build`, `lint`, and `test` tasks that use package-level scripts and Turborepo task orchestration.

## Files to Create/Modify

- `examples/cache-demo/packages/ui/package.json` (new) — Package manifest for `@cache-demo/ui` with `build`, `lint`, and `test` scripts
- `examples/cache-demo/packages/ui/src/index.ts` (new) — Barrel export file for UI components
- `examples/cache-demo/packages/ui/src/Button.tsx` (new) — A simple `Button` React component
- `examples/cache-demo/packages/ui/src/Card.tsx` (new) — A simple `Card` React component
- `examples/cache-demo/packages/ui/tsconfig.json` (new) — TypeScript configuration extending the root config
- `examples/cache-demo/turbo.json` (modify) — Add `build`, `lint`, and `test` task definitions with correct `dependsOn` and `outputs`
- `examples/cache-demo/package.json` (modify) — Add root scripts that delegate to `turbo run` for `build`, `lint`, and `test`
- `examples/cache-demo/apps/web/package.json` (modify) — Add `@cache-demo/ui` as a workspace dependency; ensure `build`, `lint`, `test` scripts exist
- `tests/test_turborepo_setup.js` (new) — Validation tests for pipeline configuration and package structure

## Requirements

### Package Structure — `packages/ui`

- `package.json` must declare `"name": "@cache-demo/ui"` with `"private": true`
- Must include `build`, `lint`, and `test` scripts in the package's own `package.json`:
  - `build`: compile TypeScript to `dist/` (e.g., `tsc`)
  - `lint`: run eslint on `src/`
  - `test`: run vitest (or jest)
- `"main"` field must point to `dist/index.js`
- `"types"` field must point to `dist/index.d.ts`
- Must declare peer dependencies on `react` and `react-dom`

### Task Pipeline — `turbo.json`

- `build` task: `dependsOn` must include `"^build"` so that dependent packages build first; `outputs` must include `"dist/**"`
- `lint` task: must be configured to run in parallel across packages with no `dependsOn` entries (or empty array); no `outputs` needed
- `test` task: `dependsOn` must include `"build"` (same-package build first); no outputs
- `dev` task: must be marked as `persistent: true` and `cache: false`
- Do NOT define task logic in the root `package.json` scripts — root scripts must only delegate via `turbo run build`, `turbo run lint`, `turbo run test`

### Root `package.json` Scripts

- `"build": "turbo run build"` (NOT `"turbo build"`)
- `"lint": "turbo run lint"`
- `"test": "turbo run test"`
- `"dev": "turbo run dev"`
- No root script may contain direct tool invocations (e.g., `tsc`, `eslint`, `next build`)

### Workspace Dependency Wiring

- `apps/web/package.json` must add `"@cache-demo/ui": "workspace:*"` to its dependencies
- The import `import { Button, Card } from "@cache-demo/ui"` must resolve after building

### Environment Variables

- `build` task in `turbo.json` must declare `env: ["NODE_ENV"]` so that different `NODE_ENV` values produce distinct cache entries
- Do not use `globalEnv` for `NODE_ENV` — scope it to the `build` task only

### Expected Functionality

- `cd examples/cache-demo && npm install && npm run build` → all packages compile successfully; `packages/ui/dist/` contains compiled JS and `.d.ts` files
- Running `npm run build` a second time without changes → Turborepo reports cache hits (`FULL TURBO`) for all packages
- Changing a file in `packages/ui/src/` and running `npm run build` → `@cache-demo/ui` rebuilds, and `apps/web` rebuilds because it depends on `@cache-demo/ui` via `^build`
- `npm run lint` → eslint runs in each package in parallel
- `npm run test` → tests in each package run after that package's build completes

## Acceptance Criteria

- `cd examples/cache-demo && npm install && npm run build` succeeds with exit code 0
- `packages/ui/dist/index.js` and `packages/ui/dist/index.d.ts` exist after build
- `turbo.json` contains `build`, `lint`, `test`, and `dev` task definitions with correct `dependsOn` and `outputs` configuration
- Root `package.json` scripts use `turbo run <task>` syntax exclusively — no direct tool invocations
- Every app/package has its own `build`, `lint`, and `test` scripts in its local `package.json`
- `@cache-demo/ui` is listed as a workspace dependency of `apps/web`
- Consecutive identical builds produce Turborepo cache hits
- The `build` task's environment variable configuration causes cache invalidation when `NODE_ENV` changes
