# Task: Configure a Turborepo Monorepo for a Design System with Web App and Documentation Site

## Background

A TypeScript monorepo needs to be configured with Turborepo for a design system project containing: a React component library (`packages/ui`), a shared utilities package (`packages/utils`), a Next.js web application (`apps/web`) that consumes the component library, and a Storybook documentation site (`apps/docs`). The configuration must set up proper task pipelines, caching, environment variable handling, and CI optimization with `--affected`.

## Files to Create/Modify

- `turbo.json` (create) — Turborepo task pipeline configuration with proper `dependsOn`, `outputs`, `inputs`, and environment variables
- `package.json` (create) — Root package.json with npm workspaces and turbo run delegation scripts
- `packages/ui/package.json` (create) — Component library package config with build, lint, test, typecheck scripts
- `packages/ui/tsconfig.json` (create) — TypeScript config for the component library
- `packages/utils/package.json` (create) — Utilities package config with build, lint, test scripts
- `apps/web/package.json` (create) — Next.js app config consuming `@myorg/ui` and `@myorg/utils`
- `apps/docs/package.json` (create) — Storybook docs app config consuming `@myorg/ui`
- `.github/workflows/ci.yml` (create) — GitHub Actions CI using `turbo run` with `--affected` for changed packages only

## Requirements

### Root `turbo.json`

- Tasks:
  - `build`: `dependsOn: ["^build"]`, `outputs: ["dist/**", ".next/**", "storybook-static/**"]`, `inputs: ["src/**", "tsconfig.json", "package.json"]`.
  - `lint`: no dependencies, `inputs: ["src/**", ".eslintrc.*", "package.json"]`, cacheable.
  - `typecheck`: `dependsOn: ["^build"]` (needs built dependencies for type resolution), `inputs: ["src/**", "tsconfig.json"]`, cacheable.
  - `test`: `dependsOn: ["build"]`, `inputs: ["src/**", "tests/**", "vitest.config.*"]`, cacheable.
  - `dev`: `dependsOn: ["^build"]`, `persistent: true`, `cache: false`.
  - `storybook`: `dependsOn: ["^build"]`, `persistent: true`, `cache: false`.

- Environment variables:
  - `build` task: `env: ["NODE_ENV"]`, `passThroughEnv: ["CI"]`.
  - `dev` task: `env: ["PORT", "NODE_ENV", "API_URL"]`.

- Global dependencies: `globalDependencies: ["tsconfig.base.json"]`.
- Global env passthrough: `globalPassThroughEnv: ["VERCEL_URL", "CI"]`.

### Root `package.json`

- `name: "@myorg/monorepo"`, `private: true`.
- Workspaces: `["apps/*", "packages/*"]`.
- Scripts — MUST delegate via `turbo run`, never contain direct task logic:
  - `"build": "turbo run build"`
  - `"lint": "turbo run lint"`
  - `"test": "turbo run test"`
  - `"typecheck": "turbo run typecheck"`
  - `"dev": "turbo run dev"`
  - `"build:affected": "turbo run build --affected"`
  - `"clean": "turbo run clean"` (not configured in turbo.json — root task)
- DevDependencies: `"turbo": "^2.7.0"`.

### Component Library (`packages/ui/package.json`)

- `name: "@myorg/ui"`, `version: "1.0.0"`.
- `main: "dist/index.js"`, `types: "dist/index.d.ts"`, `exports: { ".": { "import": "./dist/index.mjs", "require": "./dist/index.js", "types": "./dist/index.d.ts" } }`.
- Scripts:
  - `"build": "tsup src/index.ts --format cjs,esm --dts"`
  - `"lint": "eslint src/"`
  - `"test": "vitest run"`
  - `"typecheck": "tsc --noEmit"`
  - `"dev": "tsup src/index.ts --format cjs,esm --dts --watch"`
- Dependencies: `"react": "^18.3.0"`, `"react-dom": "^18.3.0"`.
- DevDependencies: `"tsup": "^8.0.0"`, `"vitest": "^2.0.0"`, `"typescript": "^5.5.0"`.
- `peerDependencies: { "react": "^18.0.0", "react-dom": "^18.0.0" }`.

### Utilities Package (`packages/utils/package.json`)

- `name: "@myorg/utils"`, `version: "1.0.0"`.
- `main: "dist/index.js"`, `types: "dist/index.d.ts"`.
- Scripts: `"build": "tsc"`, `"lint": "eslint src/"`, `"test": "vitest run"`, `"typecheck": "tsc --noEmit"`.
- No external dependencies.

### Web App (`apps/web/package.json`)

- `name: "@myorg/web"`, `version: "0.1.0"`, `private: true`.
- Dependencies: `"@myorg/ui": "workspace:*"`, `"@myorg/utils": "workspace:*"`, `"next": "^14.2.0"`, `"react": "^18.3.0"`.
- Scripts: `"build": "next build"`, `"dev": "next dev --port 3000"`, `"lint": "next lint"`, `"test": "vitest run"`, `"typecheck": "tsc --noEmit"`.

### Docs App (`apps/docs/package.json`)

- `name: "@myorg/docs"`, `version: "0.1.0"`, `private: true`.
- Dependencies: `"@myorg/ui": "workspace:*"`, `"react": "^18.3.0"`.
- Scripts: `"build": "storybook build -o storybook-static"`, `"storybook": "storybook dev -p 6006"`, `"lint": "eslint src/"`, `"test": "vitest run"`, `"typecheck": "tsc --noEmit"`.

### CI Workflow (`.github/workflows/ci.yml`)

- Trigger: `pull_request` to `main`.
- Jobs:
  1. **check** — runs on `ubuntu-latest`:
     - Checkout with `fetch-depth: 0` (needed for `--affected`).
     - Setup Node 20 with npm caching.
     - `npm ci`.
     - `turbo run lint typecheck --affected` (parallel lint + typecheck for changed packages).
  2. **test** — depends on `check`:
     - `turbo run test --affected`.
  3. **build** — depends on `check`:
     - `turbo run build --affected`.
     - Upload build artifacts.
- Uses turbo remote caching via `TURBO_TOKEN` and `TURBO_TEAM` secrets.
- Concurrency: `ci-${{ github.event.pull_request.number }}`, cancel in-progress.

### Expected Functionality

- `turbo run build` → builds `packages/utils` first, then `packages/ui` (depends on utils if imported), then `apps/web` and `apps/docs` in parallel.
- `turbo run build --affected` on a PR that only changed `packages/ui/src/Button.tsx` → builds `packages/ui`, `apps/web`, `apps/docs` (dependents), skips `packages/utils`.
- `turbo run lint` → runs lint for all 4 packages in parallel (no dependencies).
- Second run of `turbo run build` with no changes → all tasks hit cache, completes in <1 second.
- `turbo run dev` → starts `packages/ui` watch build, then `apps/web` next dev and `apps/docs` storybook dev in parallel.
- Changing `tsconfig.base.json` → invalidates cache for all tasks (global dependency).

## Acceptance Criteria

- `turbo.json` defines `build`, `lint`, `typecheck`, `test`, `dev`, and `storybook` tasks with correct `dependsOn` topology.
- `build` task declares `^build` dependency so packages build before consuming apps.
- `lint` and `typecheck` tasks are cacheable and declare correct `inputs`.
- `dev` and `storybook` tasks are `persistent: true` and `cache: false`.
- Root `package.json` uses `turbo run <task>` for all scripts — no direct task logic.
- Each package has its own build/lint/test/typecheck scripts in `package.json`.
- `packages/ui` uses `tsup` with CJS + ESM + DTS output and declares `peerDependencies`.
- `apps/web` and `apps/docs` depend on `@myorg/ui` via `workspace:*` protocol.
- CI workflow uses `--affected` to run only changed packages and their dependents.
- CI uses remote caching via `TURBO_TOKEN` and `TURBO_TEAM` environment variables.
- Environment variables are declared in `env` (cache key) or `passThroughEnv` (excluded from key) as appropriate.
