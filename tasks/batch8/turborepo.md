# Task: Create a Turborepo-Managed Monorepo with Shared UI Package and Two Apps

## Background

Vercel's Turbo repository contains examples demonstrating Turborepo's monorepo capabilities. A new example is needed that demonstrates a complete monorepo setup with two applications sharing a common UI component library, properly configured task pipelines, caching, and environment variable handling. The example must follow Turborepo's core principle of package-level tasks (not root tasks).

## Files to Create/Modify

- `examples/with-shared-ui/turbo.json` (new) — Turborepo task pipeline configuration with build, lint, test, and typecheck tasks
- `examples/with-shared-ui/package.json` (new) — Root package.json with workspaces definition and turbo-delegated scripts
- `examples/with-shared-ui/apps/web/package.json` (new) — Next.js web app package configuration with build, lint, and test scripts
- `examples/with-shared-ui/apps/web/next.config.js` (new) — Next.js configuration with transpile packages setting for the shared UI library
- `examples/with-shared-ui/apps/web/src/app/page.tsx` (new) — Main page component importing and using shared UI components
- `examples/with-shared-ui/apps/docs/package.json` (new) — Documentation site app (Next.js) package configuration
- `examples/with-shared-ui/apps/docs/next.config.js` (new) — Next.js config for docs app
- `examples/with-shared-ui/apps/docs/src/app/page.tsx` (new) — Docs page using shared UI components
- `examples/with-shared-ui/packages/ui/package.json` (new) — Shared UI library package with build and lint scripts, exporting components via package.json `exports`
- `examples/with-shared-ui/packages/ui/src/Button.tsx` (new) — Button component with variant props (primary, secondary, outline)
- `examples/with-shared-ui/packages/ui/src/Card.tsx` (new) — Card component with title, description, and optional footer
- `examples/with-shared-ui/packages/ui/src/index.ts` (new) — Barrel export for all UI components
- `examples/with-shared-ui/packages/ui/tsconfig.json` (new) — TypeScript configuration for the UI library
- `examples/with-shared-ui/packages/tsconfig/base.json` (new) — Shared TypeScript base configuration extended by all packages

## Requirements

### Turborepo Pipeline Configuration

- `turbo.json` must define tasks at the package level, not root level
- `build` task: `dependsOn: ["^build"]`, outputs `["dist/**", ".next/**"]`
- `lint` task: no dependencies, no outputs, cacheable
- `test` task: `dependsOn: ["build"]`, no outputs
- `typecheck` task: `dependsOn: ["^build"]`, no outputs
- Environment variables `NEXT_PUBLIC_API_URL` and `NODE_ENV` must be declared in the pipeline's `env` and `globalEnv` respectively

### Root Package Configuration

- Root `package.json` must define workspaces: `["apps/*", "packages/*"]`
- Root scripts must only delegate to turbo: `"build": "turbo run build"`, `"lint": "turbo run lint"`, `"test": "turbo run test"`, `"typecheck": "turbo run typecheck"`
- No task logic in root `package.json`

### Shared UI Package

- Package name: `@with-shared-ui/ui`
- `package.json` must use `exports` field to map `"."` to `"./src/index.ts"` for source access and `"./dist"` for built output
- Button component accepts props: `variant` ("primary" | "secondary" | "outline"), `size` ("sm" | "md" | "lg"), `disabled` (boolean), `children` (ReactNode)
- Card component accepts props: `title` (string), `description` (string), `footer` (optional ReactNode), `children` (ReactNode)
- Both components must be typed with explicit TypeScript interfaces exported alongside the components

### Application Packages

- Both `apps/web` and `apps/docs` must declare `@with-shared-ui/ui` as a dependency using workspace protocol (`"@with-shared-ui/ui": "workspace:*"`)
- Each app's `package.json` must define its own `build`, `lint`, and `test` scripts
- Each app's page must import and render at least the Button and Card components from `@with-shared-ui/ui`
- `next.config.js` must configure `transpilePackages: ["@with-shared-ui/ui"]`

### Expected Functionality

- Running `turbo run build` from the root builds `packages/ui` first (dependency), then `apps/web` and `apps/docs` in parallel
- Running `turbo run build --filter=@with-shared-ui/web` builds only the web app and its dependencies
- Running `turbo run lint` runs lint across all packages in parallel (no inter-package dependency)
- The second run of `turbo run build` (no changes) completes with full cache hits for all packages
- Button component renders with correct variant class: primary renders a filled button, outline renders a bordered button
- Card component renders title and description, and conditionally renders footer when provided

## Acceptance Criteria

- `turbo.json` defines build, lint, test, and typecheck tasks with correct `dependsOn` and `outputs` declarations
- Root `package.json` delegates all scripts through `turbo run` with no direct task logic
- The shared UI package exports typed Button and Card components with the specified props
- Both apps import from `@with-shared-ui/ui` using the workspace protocol dependency
- Each app and package has its own build/lint scripts in its own `package.json`
- `npm install && npx turbo run build` from the example root completes successfully
- Task pipeline respects dependency graph: `packages/ui` builds before apps
