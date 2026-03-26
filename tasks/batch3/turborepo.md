# Task: Implement Monorepo Build Pipeline with Remote Caching for Turborepo

## Background

Turborepo (https://github.com/vercel/turbo) is a high-performance build system for JavaScript/TypeScript monorepos. The project needs a monorepo example that demonstrates advanced Turborepo features: package-specific task configurations, output caching with content-aware hashing, affected-only builds triggered by file changes, and environment variable dependency declarations. This should be built within the `examples/` directory.

## Files to Create/Modify

- `examples/with-build-pipeline/turbo.json` (create) — Root Turborepo configuration with pipeline definitions, output caching, and environment variable dependencies
- `examples/with-build-pipeline/packages/ui/turbo.json` (create) — Package-specific task overrides for the UI library
- `examples/with-build-pipeline/packages/ui/package.json` (create) — UI library package definition
- `examples/with-build-pipeline/packages/ui/src/index.ts` (create) — UI library entry point
- `examples/with-build-pipeline/packages/config/turbo.json` (create) — Package-specific configuration for shared config package
- `examples/with-build-pipeline/packages/config/package.json` (create) — Config package definition
- `examples/with-build-pipeline/apps/web/package.json` (create) — Web application depending on UI and config packages
- `examples/with-build-pipeline/apps/web/turbo.json` (create) — Web app-specific task configuration
- `examples/with-build-pipeline/package.json` (create) — Root package.json with workspaces definition
- `examples/with-build-pipeline/README.md` (create) — Documentation explaining the pipeline configuration

## Requirements

### Root Pipeline Configuration

- Define tasks in `turbo.json`:
  - `build` — depends on `^build` (build dependencies first), outputs `["dist/**", ".next/**"]`, inputs `["src/**", "tsconfig.json"]`
  - `test` — depends on `build`, outputs `["coverage/**"]`, marked as `persistent: false`
  - `lint` — no dependencies, no outputs (not cacheable), runs in parallel
  - `dev` — marked as `cache: false` and `persistent: true` (long-running dev server)
- Configure global dependencies: changes to `tsconfig.base.json` or `.env` invalidate all caches
- Configure global environment variable passthrough: `NODE_ENV`, `CI`
- Set `globalDotEnv` to `[".env"]`

### Package-Specific Task Overrides

- The UI package (`packages/ui`) overrides the `build` task:
  - Additional inputs: `["../../packages/config/theme.json"]` (depends on shared theme config)
  - Additional outputs: `["storybook-static/**"]`
  - Custom environment variables: `STORYBOOK_ENV`
- The web app (`apps/web`) overrides the `build` task:
  - Environment variables: `NEXT_PUBLIC_API_URL`, `NEXT_PUBLIC_ANALYTICS_ID`
  - Outputs: `[".next/**", "!.next/cache/**"]` (cache Next.js build output but exclude the internal cache)

### Workspace Structure

- Root `package.json` with `"workspaces": ["packages/*", "apps/*"]`
- `packages/ui` depends on `packages/config` via `"@repo/config": "workspace:*"`
- `apps/web` depends on `packages/ui` via `"@repo/ui": "workspace:*"` and `packages/config`
- Each package has a `build` script, `test` script, and `lint` script in its `package.json`

### Content-Aware Hashing Demonstration

- The README explains how Turborepo computes cache keys from: file contents in `inputs`, environment variable values, task dependencies' outputs
- Document the expected behavior: changing a file in `packages/config` invalidates caches for `packages/ui` and `apps/web` (transitive dependency)
- Document that changing `NEXT_PUBLIC_API_URL` invalidates only `apps/web`'s build cache

### Expected Functionality

- `turbo run build` builds packages in dependency order: config → ui → web
- `turbo run build` on second run with no changes hits cache for all packages (outputs "cache hit")
- `turbo run build --filter=@repo/ui` builds only the UI package (and its dependency config)
- Changing `packages/config/theme.json` causes `packages/ui` and `apps/web` to rebuild on next `turbo run build`
- `turbo run lint` runs lint in all packages in parallel (no dependency ordering)
- `turbo run dev` starts persistent dev servers without caching

## Acceptance Criteria

- `turbo.json` at root defines all four tasks (build, test, lint, dev) with correct dependency, output, and input configurations
- Package-specific `turbo.json` files override task configurations with additional inputs, outputs, and environment variables
- Workspace structure has proper dependency relationships between packages
- Global dependencies and environment variables are correctly declared
- The web app excludes Next.js internal cache from cached outputs using negation pattern
- All `package.json` files have correct workspace dependency references using `workspace:*` protocol
- README accurately describes content-aware hashing behavior and cache invalidation scenarios
- The configuration is valid and parseable by Turborepo
