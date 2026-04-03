# Task: Configure an Nx Monorepo with Shared Libraries and Computation Caching

## Background

Nx (https://github.com/nrwl/nx) is a build system for monorepos with intelligent task scheduling. This task requires configuring an Nx workspace with a React frontend application, a Node.js API application, and two shared libraries (data models and utilities). The configuration must leverage Nx's computation caching, project graph dependencies, and task pipeline for optimal build performance.

## Files to Create/Modify

- `nx.json` (create) — Nx workspace configuration with task pipelines, default project settings, caching inputs/outputs, and named cache inputs for different task types.
- `workspace.json` (create) — Workspace project references pointing to all apps and libraries.
- `apps/frontend/project.json` (create) — React app project configuration with build, serve, test, and lint targets.
- `apps/api/project.json` (create) — Node.js API project configuration with build, serve, test targets.
- `libs/shared-models/project.json` (create) — Shared data models library: TypeScript interfaces and validation functions.
- `libs/shared-models/src/index.ts` (create) — Library entry exporting `User`, `Product`, `Order` interfaces and `validateUser`, `validateProduct` functions.
- `libs/utils/project.json` (create) — Shared utilities library: date formatting, string helpers, error classes.
- `libs/utils/src/index.ts` (create) — Library entry exporting utility functions.
- `libs/shared-models/src/models/user.ts` (create) — `User` interface and validation.
- `libs/shared-models/src/models/product.ts` (create) — `Product` interface and validation.
- `libs/shared-models/src/models/order.ts` (create) — `Order` interface referencing `User` and `Product`.
- `tests/test_nx_workspace_patterns.py` (create) — Tests validating workspace structure, project graphs, and caching config.

## Requirements

### Nx Configuration (`nx.json`)

```json
{
  "targetDefaults": {
    "build": {
      "dependsOn": ["^build"],
      "inputs": ["production", "^production"],
      "outputs": ["{projectRoot}/dist"],
      "cache": true
    },
    "test": {
      "inputs": ["default", "^production", "{workspaceRoot}/jest.preset.js"],
      "cache": true
    },
    "lint": {
      "inputs": ["default", "{workspaceRoot}/.eslintrc.json"],
      "cache": true
    }
  },
  "namedInputs": {
    "default": ["{projectRoot}/**/*", "sharedGlobals"],
    "production": ["default", "!{projectRoot}/**/*.spec.ts", "!{projectRoot}/tsconfig.spec.json"],
    "sharedGlobals": ["{workspaceRoot}/tsconfig.base.json"]
  },
  "defaultProject": "frontend"
}
```

### Project Dependency Graph

- `frontend` depends on `shared-models` and `utils`.
- `api` depends on `shared-models` and `utils`.
- `shared-models` depends on `utils` (for validation utility functions).
- `utils` has no internal dependencies.

### Shared Models Library

- **User**: `{ id: string, email: string, name: string, role: "admin" | "user" | "viewer", createdAt: Date }`.
- **Product**: `{ id: string, name: string, price: number, category: string, inventory: number }`.
- **Order**: `{ id: string, userId: string, items: OrderItem[], total: number, status: "pending" | "confirmed" | "shipped" | "delivered" }`.
  - `OrderItem`: `{ productId: string, quantity: number, unitPrice: number }`.
- `validateUser(data: unknown): User` — validates and returns typed User, throws `ValidationError` for invalid email (must contain `@`), empty name, or invalid role.
- `validateProduct(data: unknown): Product` — validates price > 0, inventory >= 0, non-empty name.

### Utilities Library

- `formatDate(date: Date, format: "iso" | "short" | "long"): string` — formats dates.
- `slugify(text: string): string` — converts text to URL-safe slug.
- `ValidationError` class extending `Error` with a `fields` array listing invalid field names.
- `chunk<T>(array: T[], size: number): T[][]` — splits array into chunks.
- `retry<T>(fn: () => Promise<T>, attempts: number, delayMs: number): Promise<T>` — retry async function.

### Project Configurations

- Each project defines: `build` (TypeScript compilation to `dist/`), `test` (Jest), `lint` (ESLint).
- Frontend additionally: `serve` (dev server on port 3000).
- API additionally: `serve` (Node.js dev server on port 4000).
- All projects reference `tsconfig.base.json` from workspace root.
- Tags: `frontend` → `scope:app, type:frontend`, `api` → `scope:app, type:api`, `shared-models` → `scope:shared, type:models`, `utils` → `scope:shared, type:util`.
- Workspace constraints: `type:app` can import `type:models` and `type:util`; `type:models` can import `type:util`; `type:util` cannot import from other projects.

### Expected Functionality

- `nx build frontend` → builds `utils` first, then `shared-models`, then `frontend`.
- `nx affected --target=test` (after changing `libs/utils/src/index.ts`) → runs tests for `utils`, `shared-models`, `frontend`, and `api` (all affected).
- Second run of `nx build frontend` (no changes) → cache hit, instant completion.
- `nx graph` → shows the 4-project dependency graph with correct edges.

## Acceptance Criteria

- `nx.json` configures task pipelines with correct `dependsOn`, `inputs`, `outputs`, and `cache` settings.
- All 4 projects have valid `project.json` files with build/test/lint targets.
- Shared models define typed interfaces with validation functions that throw `ValidationError`.
- Utilities provide working helper functions exported from `index.ts`.
- Project tags enforce import boundaries (apps can use shared, shared-models can use utils, utils is standalone).
- `nx build frontend` resolves dependencies in correct order.
- Tests validate workspace structure, dependency graph, caching configuration, and model validation.
