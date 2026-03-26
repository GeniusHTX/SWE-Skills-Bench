# Task: Create a Turborepo Cache Demo in the Turbo Monorepo

## Background

The Turbo repository (https://github.com/vercel/turbo) is home to Turborepo, a high-performance build system for JavaScript/TypeScript monorepos. A new example project under `examples/cache-demo/` is needed to demonstrate task pipeline configuration, dependency-aware caching, and incremental builds across multiple workspace packages.

## Files to Create

- Files under `examples/cache-demo/` including:
  - Root `package.json` with workspaces configuration
  - Root `turbo.json` with pipeline definitions
  - At least two workspace packages, each with its own `package.json` and buildable source
  - A shared library package that other packages depend on

## Requirements

### Monorepo Structure

- Configure workspaces with at least two application or library packages
- Define inter-package dependencies so building one requires its dependency to build first

### Pipeline Configuration

- Define a `turbo.json` pipeline with `build` and optionally `test` tasks
- Configure task dependencies so dependent packages build after their dependencies
- Configure appropriate cache output directories

### Buildable Packages

- Each package must have a `build` script producing output
- The shared library should export something consumed by at least one other package

## Expected Functionality

- `npm run build` invokes Turborepo, resolves the task graph, builds in dependency order, and caches outputs
- A second unchanged build hits cache and completes faster
- Modifying the shared library invalidates only affected caches

## Acceptance Criteria

- The example monorepo contains multiple packages with explicit dependency relationships and build scripts.
- Turbo runs builds in dependency order and caches outputs for unchanged packages.
- Re-running the same build without changes reuses cached work rather than rebuilding everything.
- Changing the shared package invalidates only the dependent packages' caches.
- The example makes Turbo's task graph and cache behavior easy to inspect and understand.
