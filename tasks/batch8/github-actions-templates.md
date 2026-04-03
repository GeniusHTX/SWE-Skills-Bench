# Task: Create a Reusable CI/CD Workflow Library for GitHub Actions Starter Workflows

## Background

GitHub Actions starter-workflows (https://github.com/actions/starter-workflows) is the official repository of workflow templates. The project needs a set of reusable composite action and workflow templates that implement a complete CI/CD pipeline pattern: build-test-deploy with matrix strategies, Docker image publishing with multi-platform support, security scanning, and automated release creation. These templates must be parameterized for reuse across Node.js, Python, and Go projects.

## Files to Create/Modify

- `ci/reusable-test.yml` (create) — Reusable workflow for running tests with configurable language runtime, matrix strategy over OS and language versions, artifact upload on failure, and code coverage reporting
- `ci/reusable-docker-publish.yml` (create) — Reusable workflow for building and pushing multi-platform Docker images to GHCR with layer caching, semantic version tagging, and SBOM generation
- `ci/reusable-deploy.yml` (create) — Reusable workflow for deploying to Kubernetes with environment-based approvals, rollback on health check failure, and Slack notification
- `ci/composite-setup/action.yml` (create) — Composite action that sets up language runtime, caches dependencies, and installs project dependencies for Node.js/Python/Go
- `tests/test_github_actions_templates.py` (create) — Python test suite validating workflow YAML structure, required inputs/outputs, correct action references, and security best practices

## Requirements

### Reusable Test Workflow (`reusable-test.yml`)

- Trigger: `workflow_call` with inputs:
  - `language` (string, required): `"node"`, `"python"`, or `"go"`
  - `language_versions` (string, required): JSON array of versions (e.g., `'["18", "20"]'`)
  - `os_matrix` (string, default `'["ubuntu-latest"]'`): JSON array of runner OS
  - `test_command` (string, required): Command to run tests
  - `coverage_threshold` (number, default 80): Minimum code coverage percentage
- Matrix strategy: `os × language_version` from inputs with `fail-fast: false`
- Steps: checkout, composite setup action, run linter (if configured), run tests, upload coverage artifact, fail if coverage < threshold
- Use `actions/checkout@v4`, `actions/upload-artifact@v4`
- Pin all third-party actions to full SHA, not tags

### Docker Publish Workflow (`reusable-docker-publish.yml`)

- Trigger: `workflow_call` with inputs:
  - `image_name` (string, required): Image name without registry prefix
  - `platforms` (string, default `"linux/amd64,linux/arm64"`): Target platforms
  - `dockerfile` (string, default `"Dockerfile"`): Dockerfile path
  - `build_args` (string, default `""`): Newline-separated build arguments
- Secrets: `REGISTRY_TOKEN` (required)
- Steps: checkout, set up QEMU, set up Docker Buildx, login to GHCR, extract metadata (tags and labels from Git ref), build and push with layer caching (`type=gha`), generate SBOM with `anchore/sbom-action`
- Tag strategy: `latest` for main branch, `v*` tags mapped to semver, PR builds tagged with `pr-{number}`
- The workflow must not push images on pull requests (build-only)

### Deploy Workflow (`reusable-deploy.yml`)

- Trigger: `workflow_call` with inputs:
  - `environment` (string, required): `"staging"` or `"production"`
  - `image_tag` (string, required): Docker image tag to deploy
  - `namespace` (string, required): Kubernetes namespace
  - `health_check_url` (string, required): URL to check after deployment
  - `health_check_timeout` (number, default 120): Seconds to wait for health check
- Environment: `${{ inputs.environment }}` with required reviewers for production
- Steps: configure kubectl, set image on deployment, wait for rollout, health check loop (poll URL every 10 seconds until 200 or timeout), rollback on failure (`kubectl rollout undo`)
- On success or failure, send Slack notification via webhook (secret `SLACK_WEBHOOK_URL`)

### Composite Setup Action (`composite-setup/action.yml`)

- Inputs: `language` (required), `language_version` (required), `cache_key` (default: `${{ runner.os }}-deps`)
- For `node`: use `actions/setup-node@v4` with `node-version` and `cache: npm`, then `npm ci`
- For `python`: use `actions/setup-python@v5` with `python-version` and `cache: pip`, then `pip install -r requirements.txt`
- For `go`: use `actions/setup-go@v5` with `go-version` and `cache: true`, then `go mod download`
- Output: `cache-hit` (boolean string) indicating if dependency cache was restored

### Validation Rules (for tests)

- All workflows must have `permissions` declared at the workflow level (not rely on defaults)
- No use of `actions/checkout` without pinned version (SHA or `@v4`)
- Docker builds must use `--no-cache` in CI or explicit cache configuration
- Secrets must never be logged (no `echo ${{ secrets.* }}` patterns)
- All `runs-on` values must be from an allow-list: `ubuntu-latest`, `ubuntu-22.04`, `windows-latest`, `macos-latest`
- Required `concurrency` group on deploy workflow to prevent parallel deployments

## Expected Functionality

- A Node.js project invokes `reusable-test.yml` with `language: node, language_versions: '["18","20"]', test_command: "npm test"` and gets a 2×1 matrix of test jobs
- A Docker publish triggered by pushing tag `v1.2.3` produces images tagged `1.2.3`, `1.2`, `1`, and `latest` in GHCR
- A production deploy requires manual approval, updates the Kubernetes deployment, health-checks the endpoint, and rolls back automatically if the health check fails within 120 seconds
- The composite setup action caches Node.js dependencies and reports `cache-hit: true` on subsequent runs

## Acceptance Criteria

- All workflow files are valid YAML that parse without errors
- Reusable test workflow accepts configurable language, versions, and test commands with matrix strategy
- Docker publish workflow builds multi-platform images with proper tag strategy and SBOM generation
- Deploy workflow implements health check polling and automatic rollback on failure
- Composite action supports Node.js, Python, and Go setup with dependency caching
- Security best practices: pinned action versions, declared permissions, no secret logging, concurrency control
- All tests pass with `pytest`
