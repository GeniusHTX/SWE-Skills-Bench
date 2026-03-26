# Task: Configure Nx Workspace with Module Boundaries and Affected Commands

## Background

Nx (https://github.com/nrwl/nx) is a build system with first-class monorepo support. The project needs a workspace configuration that demonstrates proper apps/libs organization, enforced module boundary rules, dependency graph constraints, and affected command configuration for efficient CI. This should be implemented as a working example within the repository's structure.

## Files to Create/Modify

- `nx.json` (modify) — Root Nx configuration with affected defaults, task runner options, caching, and target defaults
- `packages/nx/src/examples/workspace/project.json` (create) — Example app project configuration
- `packages/nx/src/examples/workspace/libs/shared-ui/project.json` (create) — Shared UI library project configuration
- `packages/nx/src/examples/workspace/libs/data-access/project.json` (create) — Data access library project configuration
- `packages/nx/src/examples/workspace/libs/util/project.json` (create) — Utility library project configuration
- `packages/nx/src/examples/workspace/.eslintrc.json` (create) — ESLint configuration with Nx module boundary rules
- `packages/nx/src/examples/workspace/tsconfig.base.json` (create) — Base TypeScript configuration with path aliases

## Requirements

### Workspace Organization

- Define a workspace with the following structure:
  - `apps/dashboard` — application (tag: `type:app`, `scope:dashboard`)
  - `libs/shared-ui` — shared UI component library (tag: `type:ui`, `scope:shared`)
  - `libs/data-access` — data access/API client library (tag: `type:data-access`, `scope:shared`)
  - `libs/util` — pure utility functions library (tag: `type:util`, `scope:shared`)
- Each project has `project.json` with: `name`, `sourceRoot`, `projectType` (`application` or `library`), `tags`, and targets for `build`, `test`, and `lint`

### Module Boundary Rules

- Configure `@nx/enforce-module-boundaries` ESLint rule with these constraints:
  - `type:app` can depend on `type:ui`, `type:data-access`, and `type:util`
  - `type:ui` can depend on `type:util` only (not `type:data-access` or `type:app`)
  - `type:data-access` can depend on `type:util` only (not `type:ui` or `type:app`)
  - `type:util` cannot depend on any other type (leaf dependency)
  - No circular dependencies allowed (`"allow": []`)
- Any violation of these rules results in an ESLint error (not warning)
- Configure the rule under `"overrides"` targeting `*.ts` and `*.tsx` files

### TypeScript Path Aliases

- Configure `tsconfig.base.json` with path aliases:
  - `@workspace/shared-ui` → `libs/shared-ui/src/index.ts`
  - `@workspace/data-access` → `libs/data-access/src/index.ts`
  - `@workspace/util` → `libs/util/src/index.ts`
- Ensure `baseUrl` is set to `"."` and `paths` use the correct relative paths

### Nx Configuration

- Configure `nx.json` with:
  - `defaultBase`: `"main"` (for affected calculations)
  - `namedInputs`: define `"production"` input excluding test files (`!{projectRoot}/**/*.spec.ts`) and `"default"` input including everything
  - `targetDefaults`: `build` uses `"production"` named input and depends on `"^build"`; `test` uses `"default"` input and depends on `"build"`
  - Task pipeline: `build` is cacheable with outputs `["{projectRoot}/dist"]`; `lint` is cacheable with no outputs; `test` is cacheable with outputs `["{projectRoot}/coverage"]`
  - `affected.defaultBase`: `"main"`

### Expected Functionality

- `nx affected:build --base=main~1` builds only projects affected by the last commit
- `nx graph` shows the dependency graph with dashboard depending on shared-ui, data-access, and util
- An import from `libs/shared-ui` to `libs/data-access` fails ESLint with module boundary violation
- An import from `libs/util` to `libs/shared-ui` fails ESLint with module boundary violation
- An import from `apps/dashboard` to `libs/shared-ui` passes ESLint
- `nx run-many --target=build` builds all projects in correct dependency order (util → shared-ui, data-access → dashboard)
- Caching: second run of `nx run-many --target=build` hits cache for unchanged projects

## Acceptance Criteria

- All four projects have valid `project.json` with correct `projectType`, `tags`, and targets
- Module boundary rules are enforced via ESLint with the correct allow/deny matrix for all type combinations
- Import from UI to data-access is an ESLint error; import from app to any lib is allowed
- TypeScript path aliases correctly resolve to library source entry points
- `nx.json` configures named inputs excluding test files from production builds
- Task pipeline defines correct dependency ordering and cacheable targets with specified outputs
- `affected.defaultBase` is set to `"main"` for CI-friendly affected calculations
- All configuration files are syntactically valid JSON
