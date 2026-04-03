# Task: Configure an Nx Workspace for a React Application with Shared Libraries

## Background

A new Nx monorepo needs to be configured for an e-commerce platform with a React frontend app, an Express API backend, and shared libraries following Nx's library type conventions (feature, ui, data-access, util). The configuration must enforce module boundaries using tags, set up cacheable targets, and optimize CI with affected commands and remote caching.

## Files to Create/Modify

- `nx.json` (create) — Nx workspace configuration with task runners, caching, named inputs, and generator defaults
- `apps/storefront/project.json` (create) — React frontend app configuration with build, serve, lint, test targets
- `apps/api/project.json` (create) — Express API app configuration
- `libs/feature-product/project.json` (create) — Feature library for product domain (smart components, business logic)
- `libs/feature-cart/project.json` (create) — Feature library for cart domain
- `libs/ui-components/project.json` (create) — UI library for presentational components
- `libs/data-access-api/project.json` (create) — Data access library for API client and state management
- `libs/util-formatting/project.json` (create) — Utility library for formatting helpers
- `.eslintrc.json` (create) — Root ESLint config with Nx module boundary rules
- `.github/workflows/ci.yml` (create) — CI workflow using `nx affected` for optimized builds
- `tsconfig.base.json` (create) — Base TypeScript config with path aliases for all libs

## Requirements

### Nx Configuration (`nx.json`)

- `npmScope: "eshop"`.
- `affected.defaultBase: "main"`.
- Named inputs:
  - `default`: `["{projectRoot}/**/*", "sharedGlobals"]`
  - `production`: `["default", "!{projectRoot}/**/?(*.)+(spec|test).[jt]s?(x)?(.snap)", "!{projectRoot}/tsconfig.spec.json", "!{projectRoot}/jest.config.[jt]s", "!{projectRoot}/.eslintrc.json"]`
  - `sharedGlobals`: `["{workspaceRoot}/babel.config.json", "{workspaceRoot}/tsconfig.base.json"]`
- Target defaults:
  - `build`: `dependsOn: ["^build"]`, `inputs: ["production", "^production"]`, `cache: true`
  - `test`: `inputs: ["default", "^production", "{workspaceRoot}/jest.preset.js"]`, `cache: true`
  - `lint`: `inputs: ["default", "{workspaceRoot}/.eslintrc.json"]`, `cache: true`
  - `e2e`: `inputs: ["default", "^production"]`, `cache: true`
- Tasks runner: `"nx/tasks-runners/default"` with `parallel: 3` and `cacheableOperations: ["build", "lint", "test", "e2e"]`.
- Generator defaults for `@nx/react`: application style `css`, linter `eslint`, bundler `webpack`; library style `css`, linter `eslint`.

### App Configurations

#### Storefront (`apps/storefront/project.json`)
- `name: "storefront"`, `projectType: "application"`, `sourceRoot: "apps/storefront/src"`.
- Tags: `["type:app", "scope:storefront"]`.
- Targets:
  - `build`: executor `@nx/webpack:webpack`, outputPath `dist/apps/storefront`, main `apps/storefront/src/main.tsx`, tsConfig `apps/storefront/tsconfig.app.json`, with production/development configurations.
  - `serve`: executor `@nx/webpack:dev-server`, depends on storefront:build, default port 4200.
  - `lint`: executor `@nx/eslint:lint`, lintFilePatterns `["apps/storefront/**/*.{ts,tsx}"]`.
  - `test`: executor `@nx/jest:jest`, jestConfig `apps/storefront/jest.config.ts`.

#### API (`apps/api/project.json`)
- `name: "api"`, `projectType: "application"`, `sourceRoot: "apps/api/src"`.
- Tags: `["type:app", "scope:api"]`.
- Targets:
  - `build`: executor `@nx/webpack:webpack`, outputPath `dist/apps/api`, main `apps/api/src/main.ts`, compiler `tsc`.
  - `serve`: executor `@nx/js:node`, buildTarget `api:build`.
  - `lint`, `test`: same pattern as storefront.

### Library Configurations

All libraries follow this tag convention:
- `libs/feature-product`: `["type:feature", "scope:product"]`
- `libs/feature-cart`: `["type:feature", "scope:cart"]`
- `libs/ui-components`: `["type:ui", "scope:shared"]`
- `libs/data-access-api`: `["type:data-access", "scope:shared"]`
- `libs/util-formatting`: `["type:util", "scope:shared"]`

Each library `project.json` has:
- `projectType: "library"`
- `build` target with `@nx/js:tsc` executor, outputPath `dist/libs/{name}`, main `libs/{name}/src/index.ts`.
- `lint` and `test` targets.

### Module Boundary Rules (`.eslintrc.json`)

- Plugin: `@nx/enforce-module-boundaries`.
- Dependency constraints:
  - `{ "sourceTag": "type:app", "onlyDependOnLibsWithTags": ["type:feature", "type:ui", "type:data-access", "type:util"] }` — apps can depend on any library type.
  - `{ "sourceTag": "type:feature", "onlyDependOnLibsWithTags": ["type:ui", "type:data-access", "type:util"] }` — features cannot depend on other features.
  - `{ "sourceTag": "type:ui", "onlyDependOnLibsWithTags": ["type:util"] }` — UI can only depend on utils.
  - `{ "sourceTag": "type:data-access", "onlyDependOnLibsWithTags": ["type:util"] }` — data access can only depend on utils.
  - `{ "sourceTag": "type:util", "onlyDependOnLibsWithTags": [] }` — utils cannot depend on anything.
  - `{ "sourceTag": "scope:storefront", "onlyDependOnLibsWithTags": ["scope:shared", "scope:product", "scope:cart"] }` — storefront scope restriction.
  - `{ "sourceTag": "scope:api", "onlyDependOnLibsWithTags": ["scope:shared"] }` — API can only use shared-scope libs.

### TypeScript Config (`tsconfig.base.json`)

- Path aliases:
  - `"@eshop/feature-product": ["libs/feature-product/src/index.ts"]`
  - `"@eshop/feature-cart": ["libs/feature-cart/src/index.ts"]`
  - `"@eshop/ui-components": ["libs/ui-components/src/index.ts"]`
  - `"@eshop/data-access-api": ["libs/data-access-api/src/index.ts"]`
  - `"@eshop/util-formatting": ["libs/util-formatting/src/index.ts"]`

### CI Workflow (`.github/workflows/ci.yml`)

- Trigger: `pull_request` on `main`.
- Steps:
  1. Checkout with `fetch-depth: 0`.
  2. Derive SHAs: `uses: nrwl/nx-set-shas@v4`.
  3. `npm ci`.
  4. `npx nx affected -t lint test build --parallel=3`.
- Remote caching: `NX_CLOUD_ACCESS_TOKEN` secret, `npx nx-cloud start-ci-run` before affected command.

### Expected Functionality

- `nx run storefront:build` → builds `util-formatting`, `data-access-api`, `ui-components`, `feature-product`, `feature-cart` (dependencies), then storefront.
- `nx affected -t test` on a PR changing `libs/ui-components/src/Button.tsx` → tests `ui-components`, `feature-product`, `feature-cart`, `storefront`, `docs` (transitive dependents). Skips `api`, `util-formatting`, `data-access-api`.
- `nx lint storefront` with an import from `feature-product` → passes (apps can depend on features).
- `nx lint ui-components` with an import from `feature-cart` → fails module boundary check (UI cannot depend on feature).
- `nx lint api` with an import from `feature-product` → fails (API scope cannot access product scope).

## Acceptance Criteria

- `nx.json` configures cacheable operations (build, lint, test, e2e) with correct named inputs separating production from test files.
- Build target uses `^build` dependency for proper topological ordering.
- All 7 projects have `project.json` with correct `projectType`, `tags`, and target configurations.
- Module boundary rules enforce the dependency hierarchy: app → feature → ui/data-access → util.
- Scope tags prevent cross-scope imports (e.g., API app cannot import product-scoped libraries).
- `tsconfig.base.json` defines path aliases for all libraries under `@eshop/` prefix.
- CI workflow uses `nx affected` with derived SHAs to build/test/lint only changed projects.
- Remote caching is configured via `NX_CLOUD_ACCESS_TOKEN`.
- Task runner parallelism is set to 3.
