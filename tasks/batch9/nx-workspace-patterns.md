# Task: Configure an Nx Monorepo Workspace with Project Boundaries and Build Caching

## Background

Nx (https://github.com/nrwl/nx) is a build system for monorepos. A new workspace configuration is needed that sets up a multi-project monorepo with two applications (a React web app and a Node.js API) and four shared libraries (ui, utils, data-access, types), with proper project boundaries using tags and module boundary lint rules, optimized build caching, task pipelines with dependency ordering, and affected command configuration.

## Files to Create/Modify

- `nx.json` (create) — Root Nx configuration with task runner options, named inputs, target defaults for build/test/lint, affected configuration, and cache settings
- `project.json` (create at `apps/web/project.json`) — React web app project configuration with build, serve, test, and lint targets
- `project.json` (create at `apps/api/project.json`) — Node.js API project configuration with build, serve, test targets
- `project.json` (create at `libs/shared/ui/project.json`) — UI library configuration with build, test, lint targets and `type:ui` tag
- `project.json` (create at `libs/shared/utils/project.json`) — Utils library configuration with `type:util` tag
- `project.json` (create at `libs/shared/data-access/project.json`) — Data-access library with `type:data-access` tag
- `project.json` (create at `libs/shared/types/project.json`) — Types library with `type:types` tag
- `.eslintrc.json` (create) — Root ESLint config with `@nx/enforce-module-boundaries` rule defining allowed dependency constraints between project tags
- `tsconfig.base.json` (create) — Root TypeScript config with path aliases for all libraries (`@myorg/ui`, `@myorg/utils`, `@myorg/data-access`, `@myorg/types`)

## Requirements

### Root Nx Configuration (`nx.json`)

- `npmScope: "myorg"`
- `affected.defaultBase: "main"`
- `tasksRunnerOptions.default`:
  - `runner: "nx/tasks-runners/default"`
  - `options.cacheableOperations: ["build", "lint", "test", "e2e"]`
  - `options.parallel: 3`
- `targetDefaults`:
  - `build`: `dependsOn: ["^build"]`, `inputs: ["production", "^production"]`, `cache: true`
  - `test`: `inputs: ["default", "^production", "{workspaceRoot}/jest.preset.js"]`, `cache: true`
  - `lint`: `inputs: ["default", "{workspaceRoot}/.eslintrc.json"]`, `cache: true`
- `namedInputs`:
  - `default`: `["{projectRoot}/**/*", "sharedGlobals"]`
  - `production`: `["default", "!{projectRoot}/**/?(*.)+(spec|test).[jt]s?(x)?(.snap)", "!{projectRoot}/tsconfig.spec.json", "!{projectRoot}/jest.config.[jt]s"]`
  - `sharedGlobals`: `["{workspaceRoot}/tsconfig.base.json"]`

### Application Projects

**Web App (`apps/web/project.json`)**:
- `name: "web"`, `projectType: "application"`, `sourceRoot: "apps/web/src"`
- `tags: ["type:app", "scope:web"]`
- `targets.build`: executor `@nx/webpack:webpack`, options `outputPath: "dist/apps/web"`, `main: "apps/web/src/main.tsx"`, `tsConfig: "apps/web/tsconfig.app.json"`
- `targets.serve`: executor `@nx/webpack:dev-server`, options `buildTarget: "web:build"`
- `targets.test`: executor `@nx/jest:jest`, options `jestConfig: "apps/web/jest.config.ts"`
- `targets.lint`: executor `@nx/eslint:lint`
- `implicitDependencies: ["types"]`

**API (`apps/api/project.json`)**:
- `name: "api"`, `projectType: "application"`, `sourceRoot: "apps/api/src"`
- `tags: ["type:app", "scope:api"]`
- `targets.build`: executor `@nx/js:tsc`, options `outputPath: "dist/apps/api"`, `main: "apps/api/src/main.ts"`, `tsConfig: "apps/api/tsconfig.app.json"`
- `targets.serve`: executor `@nx/js:node`, options `buildTarget: "api:build"`
- `targets.test`: executor `@nx/jest:jest`

### Shared Libraries

Each library project must include:
- `projectType: "library"`, appropriate `tags`
- `targets.build`: executor `@nx/js:tsc` with `outputPath: "dist/libs/shared/<name>"`
- `targets.test`: executor `@nx/jest:jest`
- `targets.lint`: executor `@nx/eslint:lint`

Tag assignments:
- `libs/shared/ui`: `["type:ui", "scope:shared"]`
- `libs/shared/utils`: `["type:util", "scope:shared"]`
- `libs/shared/data-access`: `["type:data-access", "scope:shared"]`
- `libs/shared/types`: `["type:types", "scope:shared"]`

### Module Boundary Rules (`.eslintrc.json`)

- Rule `@nx/enforce-module-boundaries` with `enforceBuildableLibDependency: true`
- Dependency constraints:
  - `type:app` can depend on `type:ui`, `type:data-access`, `type:util`, `type:types`
  - `type:ui` can depend on `type:util`, `type:types`
  - `type:data-access` can depend on `type:util`, `type:types`
  - `type:util` can depend on `type:types` only
  - `type:types` cannot depend on any other type
- `depConstraints` array with `sourceTag` and `onlyDependOnLibsWithTags` for each type
- `allow: []` (no blanket exceptions)

### TypeScript Path Aliases (`tsconfig.base.json`)

- `compilerOptions.baseUrl: "."`
- `compilerOptions.paths`:
  - `"@myorg/ui": ["libs/shared/ui/src/index.ts"]`
  - `"@myorg/utils": ["libs/shared/utils/src/index.ts"]`
  - `"@myorg/data-access": ["libs/shared/data-access/src/index.ts"]`
  - `"@myorg/types": ["libs/shared/types/src/index.ts"]`

### Expected Functionality

- `nx build web` triggers `build` on all library dependencies first (`^build` dependency)
- `nx affected --target=test --base=main` only runs tests for projects affected by changes
- Importing `@myorg/data-access` from a `type:ui` tagged library fails the lint boundary check
- Importing `@myorg/types` from any project succeeds (types is universally allowed)
- Build cache correctly stores and retrieves results for unchanged projects

## Acceptance Criteria

- `nx.json` configures caching for build/test/lint with correct named inputs
- All 6 project configs have correct executors, tags, and source roots
- Module boundary rules enforce the dependency hierarchy: app → feature libs → util → types
- `type:types` projects have no allowed dependencies (enforced by eslint rule)
- TypeScript path aliases resolve correctly for all 4 shared libraries
- `pnpm install && pnpm build` succeeds
- `python -m pytest /workspace/tests/test_nx_workspace_patterns.py -v --tb=short` passes
