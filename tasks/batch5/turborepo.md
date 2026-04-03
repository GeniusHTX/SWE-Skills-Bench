# Task: Configure a Turborepo Monorepo with Shared Packages and Pipeline Caching

## Background

Turbo (https://github.com/vercel/turbo) provides a high-performance build system for JavaScript/TypeScript monorepos. This task requires setting up a Turborepo monorepo structure with a shared UI component library, a shared TypeScript configuration package, a Next.js web app, and an Express API server. The build pipeline must use Turborepo's caching and task dependency features to minimize rebuild time.

## Files to Create/Modify

- `examples/with-shared-packages/turbo.json` (create) — Turborepo pipeline configuration defining `build`, `lint`, `test`, and `dev` tasks with proper dependency ordering, caching, and output declarations.
- `examples/with-shared-packages/package.json` (create) — Root package.json with workspaces definition, shared devDependencies, and turbo scripts.
- `examples/with-shared-packages/packages/ui/package.json` (create) — Shared UI library package with TypeScript and React as peer dependencies.
- `examples/with-shared-packages/packages/ui/src/index.ts` (create) — UI library entry point exporting `Button`, `Card`, and `Input` components.
- `examples/with-shared-packages/packages/ui/src/Button.tsx` (create) — Button component with variants (primary, secondary, outline) and sizes (sm, md, lg).
- `examples/with-shared-packages/packages/tsconfig/base.json` (create) — Shared TypeScript base configuration with strict settings.
- `examples/with-shared-packages/packages/tsconfig/react.json` (create) — React-specific tsconfig extending base, enabling JSX.
- `examples/with-shared-packages/packages/tsconfig/package.json` (create) — Package definition for the shared tsconfig.
- `examples/with-shared-packages/apps/web/package.json` (create) — Next.js app depending on `@repo/ui` and `@repo/tsconfig`.
- `examples/with-shared-packages/apps/api/package.json` (create) — Express API server depending on `@repo/tsconfig`.
- `examples/with-shared-packages/apps/api/src/index.ts` (create) — Express server with a `/health` endpoint and a `/api/items` CRUD endpoint.
- `tests/test_turborepo.py` (create) — Tests validating turbo.json configuration, package dependency graph, and workspace structure.

## Requirements

### Turborepo Pipeline (`turbo.json`)

```json
{
  "$schema": "https://turbo.build/schema.json",
  "globalDependencies": ["**/.env.*local"],
  "pipeline": {
    "build": {
      "dependsOn": ["^build"],
      "outputs": ["dist/**", ".next/**"],
      "cache": true
    },
    "lint": {
      "dependsOn": ["^build"],
      "cache": true
    },
    "test": {
      "dependsOn": ["build"],
      "outputs": ["coverage/**"],
      "cache": true
    },
    "dev": {
      "cache": false,
      "persistent": true
    }
  }
}
```
- `build` depends on upstream package builds (`"^build"`) ensuring UI library builds before the apps.
- `test` depends on local `build` task completing first.
- `dev` is not cached and marked as persistent for long-running dev servers.

### Workspace Structure

- Root: `"workspaces": ["packages/*", "apps/*"]`.
- Package naming convention: `@repo/ui`, `@repo/tsconfig`.
- Apps: `@repo/web`, `@repo/api`.

### Shared UI Library

- `Button` component: props `variant: "primary" | "secondary" | "outline"`, `size: "sm" | "md" | "lg"`, `onClick`, `children`, `disabled`.
- `Card` component: props `title`, `children`, `footer` (optional).
- `Input` component: props `label`, `value`, `onChange`, `type: "text" | "email" | "password"`, `error` (optional string).
- Package uses TypeScript with declaration output to `dist/`.
- Build script: `tsc --declaration --outDir dist`.

### Shared TypeScript Config

- `base.json`: `strict: true`, `esModuleInterop: true`, `skipLibCheck: true`, `forceConsistentCasingInFileNames: true`, `resolveJsonModule: true`, `isolatedModules: true`.
- `react.json`: extends `./base.json`, adds `"jsx": "react-jsx"`, `"lib": ["dom", "dom.iterable", "esnext"]`.

### Express API

- `/health` → `{ status: "ok", uptime: process.uptime() }`.
- `/api/items` → CRUD with in-memory storage: GET (list), POST (create), GET /:id (read), PUT /:id (update), DELETE /:id (remove).
- Each item: `{ id: string, name: string, createdAt: string }`.
- Uses `@repo/tsconfig` base configuration.

### Expected Functionality

- `turbo run build` → builds `@repo/ui` first, then `@repo/web` and `@repo/api` in parallel.
- Second run of `turbo run build` (no changes) → cached, completes in <1s.
- Changing a file in `@repo/ui` → rebuilds UI, then rebuilds dependent apps, but leaves API cache intact if API doesn't depend on the changed UI export.
- `turbo run dev --filter=@repo/web` → starts only the web dev server.

## Acceptance Criteria

- `turbo.json` defines correct pipeline with dependency ordering, outputs, and cache settings.
- Workspace structure follows monorepo conventions with `packages/` and `apps/`.
- UI library exports typed React components with proper TypeScript declarations.
- Shared tsconfig provides reusable base and React-specific configurations.
- Express API provides a working CRUD endpoint with in-memory storage.
- `turbo run build` succeeds and second run uses cache.
- Tests verify turbo.json structure, workspace dependencies, and package.json correctness.
