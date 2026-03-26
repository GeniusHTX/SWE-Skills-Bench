# Task: Create Monorepo CI/CD Starter Workflow for Full-Stack TypeScript Projects

## Background

The starter-workflows repository (https://github.com/actions/starter-workflows) provides official GitHub Actions workflow templates that appear in the "Actions" tab of any GitHub repository. There is currently no starter workflow template designed for full-stack TypeScript monorepo projects that need to build, lint, test, and deploy multiple packages (e.g., a backend API and a frontend app) with shared dependencies and conditional job execution. A new CI workflow template and a corresponding deployment workflow template need to be added to fill this gap.

## Files to Create/Modify

- `ci/typescript-monorepo.yml` (create) — CI workflow template for TypeScript monorepo: install, lint, test, build across multiple packages with path-based conditional jobs
- `ci/properties/typescript-monorepo.properties.json` (create) — Metadata file for the CI workflow template (name, description, icon, categories)
- `deployments/typescript-monorepo-deploy.yml` (create) — Deployment workflow template that builds Docker images per package and deploys to a container registry
- `deployments/properties/typescript-monorepo-deploy.properties.json` (create) — Metadata file for the deployment workflow template

## Requirements

### CI Workflow (`ci/typescript-monorepo.yml`)

- Trigger on `push` to `$default-branch` and on `pull_request` targeting `$default-branch`
- Define a `changes` job that uses `dorny/paths-filter` (or equivalent action) to detect which packages have changed; output boolean flags for `backend`, `frontend`, and `shared`
- Define a `lint` job that runs on every trigger: checkout, setup Node.js with `${{ matrix.node-version }}` using `actions/setup-node@v4` with `cache: 'npm'`, install dependencies with `npm ci`, and run `npm run lint`
- Define `test-backend` and `test-frontend` jobs that are conditional on the `changes` job output; each job:
  - Has a `needs: [changes, lint]` dependency
  - Uses a matrix strategy over Node.js versions `[18.x, 20.x]`
  - Runs `npm ci` and then the package-specific test command (`npm run test --workspace=packages/backend` or `npm run test --workspace=packages/frontend`)
  - Uploads test coverage artifacts using `actions/upload-artifact@v4`
- Define a `build` job that needs `[test-backend, test-frontend]` (with `if: always()` to handle skipped conditional jobs), runs `npm run build`, and uploads the build output as an artifact
- Set appropriate `permissions` at the workflow level: `contents: read`, `checks: write`
- Use `actions/checkout@v4` and `actions/setup-node@v4` throughout
- Include `concurrency` settings that cancel in-progress runs for the same branch/PR

### Deployment Workflow (`deployments/typescript-monorepo-deploy.yml`)

- Trigger on `push` to `$default-branch` and on tags matching `v*`
- Define environment variables: `REGISTRY: ghcr.io`, `IMAGE_NAME: ${{ github.repository }}`
- Include a `build-and-push` job with appropriate permissions (`contents: read`, `packages: write`)
- Use `docker/login-action@v3` to authenticate with the container registry
- Use `docker/metadata-action@v5` to generate image tags with `type=ref,event=branch`, `type=ref,event=pr`, `type=semver,pattern={{version}}`, and `type=semver,pattern={{major}}.{{minor}}`
- Use `docker/build-push-action@v5` to build and push with GitHub Actions cache (`cache-from: type=gha`, `cache-to: type=gha,mode=max`)
- Include a separate `deploy` job that runs after `build-and-push`, uses an `environment: production` setting, and has placeholder steps for deployment commands

### Properties Files

- The CI properties file must contain: `name` (unique, descriptive), `description`, `iconName` set to `nodejs`, and `categories` including `Continuous integration`, `JavaScript`, `TypeScript`, and `npm`
- The deployment properties file must contain: `name`, `description`, `iconName` set to `docker`, and `categories` including `deployment` and `JavaScript`
- Both properties files must be valid JSON and follow the existing repository convention (see `ci/properties/node.js.properties.json` as reference)

### Workflow YAML Conventions

- All actions must use pinned major versions (e.g., `@v4`, not `@latest` or `@main`)
- Use `$default-branch` variable for branch references
- Include meaningful `name` fields on every step for readability
- Avoid hardcoded secrets; use `${{ secrets.GITHUB_TOKEN }}` for registry authentication

### Expected Functionality

- When a PR changes only `packages/backend/`, only `test-backend` runs; `test-frontend` is skipped
- When a PR changes `packages/shared/`, both `test-backend` and `test-frontend` run (since shared code affects both)
- When a PR changes only documentation files (e.g., `README.md`), `lint` still runs but both test jobs are skipped; `build` still runs with `if: always()`
- When a push to the default branch includes a semver tag `v1.2.3`, the deployment workflow generates Docker image tags `1.2.3` and `1.2`
- Concurrent pushes to the same branch cancel the older in-progress workflow run

## Acceptance Criteria

- `ci/typescript-monorepo.yml` is valid YAML that defines the `changes`, `lint`, `test-backend`, `test-frontend`, and `build` jobs with correct triggers, dependencies, and conditional execution
- Path-based change detection correctly gates `test-backend` and `test-frontend` jobs based on which packages were modified
- Matrix strategy tests against Node.js 18.x and 20.x for both package test jobs
- `deployments/typescript-monorepo-deploy.yml` is valid YAML that builds and pushes Docker images with correct tags derived from branch, PR, and semver tag events
- Both properties JSON files are valid and contain the required `name`, `description`, `iconName`, and `categories` fields
- All actions use pinned major-version references, and no hardcoded secrets are present
- Concurrency settings are configured to cancel in-progress runs for the same ref
