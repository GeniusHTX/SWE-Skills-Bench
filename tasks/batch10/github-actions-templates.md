# Task: Create CI/CD Starter Workflows for a Full-Stack Node.js Application

## Background

The starter-workflows repository (https://github.com/actions/starter-workflows) provides reusable GitHub Actions workflow templates organized in `ci/`, `deployments/`, `automation/`, and `code-scanning/` directories. Three new production-quality workflow files are needed: a CI test workflow with matrix builds, a Docker build-and-push deployment workflow, and an automated release workflow with approval gates.

## Files to Create/Modify

- `ci/node-fullstack-ci.yml` (new) — CI workflow: lint, test, and build across multiple Node.js versions and OS platforms
- `deployments/docker-ghcr-deploy.yml` (new) — Build a Docker image, push to GitHub Container Registry (ghcr.io), and deploy to a staging environment
- `automation/release-please.yml` (new) — Automated release workflow triggered by version tags with changelog generation and approval gates
- `tests/test_workflows.py` (new) — Validation tests that parse the YAML files and verify structure, required fields, and correctness

## Requirements

### CI Workflow — `ci/node-fullstack-ci.yml`

- Trigger on `push` to `main` and `develop` branches, and on `pull_request` to `main`
- Define a `test` job with a strategy matrix:
  - `node-version`: `[18.x, 20.x, 22.x]`
  - `os`: `[ubuntu-latest, windows-latest]`
- Steps must include, in order:
  1. `actions/checkout@v4`
  2. `actions/setup-node@v4` with `node-version: ${{ matrix.node-version }}` and `cache: "npm"`
  3. `npm ci` for dependency installation
  4. `npm run lint` for linting
  5. `npm test -- --coverage` for test execution
  6. Upload test coverage artifact using `actions/upload-artifact@v4` with name `coverage-${{ matrix.os }}-${{ matrix.node-version }}`
- Define a separate `build` job that `needs: [test]` and runs only on `ubuntu-latest` with Node.js `20.x`:
  1. Checkout, setup node, install
  2. `npm run build`
  3. Upload build output artifact with path `dist/`
- Both jobs must set `timeout-minutes: 15`

### Deployment Workflow — `deployments/docker-ghcr-deploy.yml`

- Trigger on push to `main` branch and on tags matching `v*`
- Set workflow-level `env` variables: `REGISTRY: ghcr.io` and `IMAGE_NAME: ${{ github.repository }}`
- Define a `build-and-push` job with `permissions: { contents: read, packages: write }`
- Steps:
  1. `actions/checkout@v4`
  2. `docker/login-action@v3` with registry `${{ env.REGISTRY }}`, username `${{ github.actor }}`, password `${{ secrets.GITHUB_TOKEN }}`
  3. `docker/metadata-action@v5` to extract tags and labels — tags must include `type=ref,event=branch`, `type=semver,pattern={{version}}`, and `type=semver,pattern={{major}}.{{minor}}`
  4. `docker/build-push-action@v5` with `push: true`, tags and labels from metadata step, and build cache using `cache-from: type=gha` and `cache-to: type=gha,mode=max`
- Define a `deploy-staging` job that `needs: [build-and-push]` and uses `environment: staging`:
  1. Print deployed image tag for verification

### Release Workflow — `automation/release-please.yml`

- Trigger on push of tags matching `v[0-9]+.[0-9]+.[0-9]+`
- Define a `release` job with `permissions: { contents: write }`
- Steps:
  1. `actions/checkout@v4` with `fetch-depth: 0` (full history for changelog)
  2. `actions/setup-node@v4` with `node-version: 20.x`
  3. `npm ci && npm run build`
  4. Create a GitHub release using `softprops/action-gh-release@v2` with `generate_release_notes: true` and upload `dist/` contents as release assets
- Define a `deploy-production` job that `needs: [release]` with `environment: production` (requires manual approval):
  1. Print release version for verification

### Workflow Quality

- All workflows must use pinned action versions (e.g., `@v4`, not `@latest` or `@main`)
- All secrets must be referenced via `${{ secrets.* }}` — no hardcoded credentials
- All jobs must specify `runs-on` explicitly
- Reusable patterns: dependency caching via `actions/setup-node@v4`'s `cache` parameter, not manual cache steps

### Expected Functionality

- `node-fullstack-ci.yml` produces a 6-cell matrix (3 Node versions × 2 OS) where each cell runs lint, test, and coverage upload independently
- `docker-ghcr-deploy.yml` tags images with both branch name and semver on tag pushes
- `release-please.yml` creates a GitHub release with generated notes only on semver tag pushes
- `deploy-production` job does not run until the `release` job completes and environment approval is granted

### Edge Cases

- CI workflow must not fail the entire matrix if a single cell fails — set `strategy.fail-fast: false`
- Docker build must work for both branch pushes (tagged with branch name) and version tag pushes (tagged with semver)
- Release workflow must handle the case where `dist/` does not exist by running `npm run build` before upload

## Acceptance Criteria

- All three workflow files are valid YAML and parse without errors
- `ci/node-fullstack-ci.yml` defines a matrix strategy producing 6 job combinations across Node.js versions and operating systems
- `deployments/docker-ghcr-deploy.yml` authenticates to `ghcr.io`, builds with layer caching, pushes with semver and branch tags, and triggers a staging deployment
- `automation/release-please.yml` creates a GitHub release with auto-generated notes and uploads build artifacts on semver tags
- All action references use specific version tags, not `@latest` or branch references
- No workflow file contains hardcoded secrets or credentials
- The production deployment job requires completion of prior jobs and uses a named environment for approval gating
- Tests in `tests/test_workflows.py` pass, validating YAML structure, required keys, action versions, and job dependency chains
