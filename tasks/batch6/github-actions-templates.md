# Task: Create GitHub Actions CI/CD Workflows for a Full-Stack TypeScript Application

## Background

A full-stack TypeScript application with a Next.js frontend and Express API backend needs a complete GitHub Actions CI/CD setup. The project uses npm workspaces with packages at `apps/web` and `apps/api`. Workflows are needed for pull request testing (matrix build across Node 18/20), Docker image building and pushing to GHCR, and Kubernetes deployment with staging/production environments.

## Files to Create/Modify

- `.github/workflows/ci.yml` (create) — Pull request CI: lint, test, build across Node 18.x and 20.x matrix
- `.github/workflows/build-push.yml` (create) — Build and push Docker images for web and api to GitHub Container Registry on main branch pushes and version tags
- `.github/workflows/deploy.yml` (create) — Deploy to Kubernetes: staging on main push, production on manual dispatch with approval
- `.github/workflows/security.yml` (create) — Weekly security scan: npm audit, Trivy container scan, CodeQL analysis
- `.github/actions/setup-node/action.yml` (create) — Composite action for Node.js setup with npm caching, shared across workflows

## Requirements

### CI Workflow (`.github/workflows/ci.yml`)

- Trigger: `push` to `main` and `develop` branches; `pull_request` targeting `main`.
- Jobs:
  1. **lint** — runs on `ubuntu-latest`, uses composite action for Node setup, runs `npm run lint` at workspace root.
  2. **test** — matrix strategy: `node-version: [18.x, 20.x]`, `package: [web, api]` (4 combinations). Runs `npm test --workspace=apps/${{ matrix.package }}`. Uploads coverage to Codecov with flag `${{ matrix.package }}-node${{ matrix.node-version }}`.
  3. **build** — depends on `lint` and `test`. Runs `npm run build` at workspace root. Uploads `apps/web/.next/` and `apps/api/dist/` as artifacts with 1-day retention.
- Concurrency: cancel in-progress runs for the same branch (`concurrency: group: ci-${{ github.ref }}, cancel-in-progress: true`).

### Build & Push Workflow (`.github/workflows/build-push.yml`)

- Trigger: `push` to `main`; `push` of tags matching `v*`.
- Environment variables: `REGISTRY: ghcr.io`, `IMAGE_BASE: ghcr.io/${{ github.repository }}`.
- Jobs (run in parallel):
  1. **build-web** — builds `apps/web/Dockerfile`, pushes to `$IMAGE_BASE/web`. Tags: branch name, SHA short, semver from tag (if tag push). Uses `docker/build-push-action@v5` with GitHub Actions cache (`cache-from: type=gha`, `cache-to: type=gha,mode=max`).
  2. **build-api** — same pattern for `apps/api/Dockerfile`, pushes to `$IMAGE_BASE/api`.
- Both jobs use `docker/metadata-action@v5` for tag extraction with patterns: `type=ref,event=branch`, `type=sha`, `type=semver,pattern={{version}}`, `type=semver,pattern={{major}}.{{minor}}`.
- Permissions: `contents: read`, `packages: write`.

### Deploy Workflow (`.github/workflows/deploy.yml`)

- Trigger: `workflow_run` completion of build-push workflow (for staging); `workflow_dispatch` with input `environment` (choice: `staging`, `production`) for manual deploy.
- Jobs:
  1. **deploy-staging** — runs on workflow_run trigger. Uses `aws-actions/configure-aws-credentials@v4` and `aws eks update-kubeconfig`. Runs `kubectl set image deployment/web web=$IMAGE_BASE/web:$SHA` and `kubectl set image deployment/api api=$IMAGE_BASE/api:$SHA` in namespace `staging`. Waits for rollout with `kubectl rollout status --timeout=300s`.
  2. **deploy-production** — runs on workflow_dispatch when `environment == 'production'`. Same kubectl pattern but namespace `production`. Uses GitHub environment `production` with required reviewers.
- Both jobs output deployment URL as job output and post status to a Slack webhook (`SLACK_WEBHOOK_URL` secret).

### Security Workflow (`.github/workflows/security.yml`)

- Trigger: `schedule` cron `0 6 * * 1` (Mondays at 6 AM UTC); `workflow_dispatch`.
- Jobs:
  1. **audit** — runs `npm audit --audit-level=moderate`, allows failure but creates a GitHub issue if vulnerabilities found using `peter-evans/create-issue-from-file@v4`.
  2. **trivy** — scans both Docker images with `aquasecurity/trivy-action@master`, uploads SARIF results to GitHub Security tab.
  3. **codeql** — uses `github/codeql-action` to analyze JavaScript/TypeScript code.

### Composite Action (`.github/actions/setup-node/action.yml`)

- Inputs: `node-version` (default `"20.x"`).
- Steps: `actions/checkout@v4`, `actions/setup-node@v4` with npm caching, `npm ci`.
- Used by ci.yml and deploy.yml workflows.

### Expected Functionality

- Opening a PR → ci.yml runs lint, 4 test matrix jobs, and build in sequence.
- Pushing to `main` → ci.yml runs, then build-push.yml builds 2 Docker images and pushes to GHCR, then deploy.yml deploys to staging.
- Pushing tag `v1.2.3` → build-push.yml tags images with `1.2.3` and `1.2`.
- Manual workflow_dispatch with `environment: production` → deploys to production namespace after reviewer approval.
- Monday 6 AM → security.yml runs audit, Trivy, and CodeQL scans.

## Acceptance Criteria

- CI workflow runs lint, test (4 matrix combinations), and build jobs with proper dependencies (`build` needs `lint` and `test`).
- Test matrix covers Node 18.x and 20.x for both `web` and `api` packages, with per-combination coverage flags.
- Build & push workflow produces Docker images with correct multi-pattern tags (branch, SHA, semver) and uses GHA build cache.
- Deploy workflow separates staging (automatic) from production (manual with environment protection).
- Security workflow runs on weekly schedule and creates issues for npm audit findings.
- Composite action is reused across workflows for consistent Node.js setup.
- Concurrency settings prevent duplicate CI runs on the same branch.
