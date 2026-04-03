# Task: Create GitHub Actions Reusable Workflow Templates for a CI/CD Pipeline

## Background

The GitHub Actions starter-workflows repository (https://github.com/actions/starter-workflows) provides template workflows. This task requires creating a set of reusable workflow templates for a Python web application CI/CD pipeline: a CI workflow (lint, test, build), a CD workflow (deploy to staging/production), a security scanning workflow, and a reusable workflow for Docker image building that is callable from other workflows.

## Files to Create/Modify

- `ci/python-webapp-ci.yml` (create) — CI workflow: triggered on push/PR to main. Jobs: lint (ruff + mypy), test (pytest with coverage matrix for Python 3.11/3.12), build (Docker image build and push to GHCR).
- `deployments/python-webapp-deploy.yml` (create) — CD workflow: triggered on workflow_dispatch with environment input (staging/production). Calls the reusable Docker build workflow, then deploys to the selected environment with approval gates.
- `code-scanning/python-security-scan.yml` (create) — Security workflow: scheduled daily + on PR. Jobs: dependency audit (pip-audit), SAST (bandit), secret scanning (gitleaks), SBOM generation (syft).
- `ci/docker-build-reusable.yml` (create) — Reusable workflow (`workflow_call`) for building and pushing Docker images. Inputs: image_name, tag, dockerfile_path, build_args. Outputs: image_digest, image_uri. Uses Docker layer caching.
- `tests/test_github_actions_templates.py` (create) — Tests validating YAML syntax, required fields, correct trigger events, job dependency ordering, and secret references.

## Requirements

### CI Workflow (`python-webapp-ci.yml`)

- Trigger: `push` to `main`, `pull_request` to `main`.
- **Job: lint** — runs on `ubuntu-latest`:
  - Checkout code, setup Python 3.12, install dependencies from `requirements-dev.txt`.
  - Run `ruff check .` (linting) and `ruff format --check .` (formatting).
  - Run `mypy src/ --strict`.
- **Job: test** — matrix strategy for Python `[3.11, 3.12]`:
  - Setup Python from matrix, install dependencies.
  - Run `pytest tests/ --cov=src --cov-report=xml --junitxml=results.xml`.
  - Upload coverage report as artifact.
  - Upload test results for PR annotation using `dorny/test-reporter`.
- **Job: build** — needs `[lint, test]`, runs only on push to main (not PRs):
  - Uses the reusable `docker-build-reusable.yml` workflow.
  - Passes `image_name: ghcr.io/${{ github.repository }}`, `tag: ${{ github.sha }}`.
- Concurrency: group by PR number, cancel in-progress.

### CD Workflow (`python-webapp-deploy.yml`)

- Trigger: `workflow_dispatch` with input `environment` (choice: staging, production).
- **Job: build** — uses `docker-build-reusable.yml` with tag from the last successful CI run.
- **Job: deploy-staging** — if `environment == 'staging'`, environment `staging` (no approval required), deploys using `kubectl set image`.
- **Job: deploy-production** — if `environment == 'production'`, environment `production` (requires reviewers), needs `deploy-staging` to succeed first. Uses `kubectl set image` with rollout status check.
- Both deploy jobs use a Kubernetes service account token stored in environment secrets (`KUBE_CONFIG`).

### Security Scan Workflow

- Trigger: `schedule` (daily at 06:00 UTC), `pull_request`.
- **Job: dependency-audit** — `pip-audit --requirement requirements.txt --format json --output audit.json`. Upload as artifact. Fail on critical vulnerabilities.
- **Job: sast** — `bandit -r src/ -f json -o bandit.json`. Upload as artifact.
- **Job: secret-scan** — `gitleaks detect --report-format json --report-path gitleaks.json`.
- **Job: sbom** — `syft . -o spdx-json > sbom.json`. Upload as artifact.
- **Job: report** — needs all above, runs always. Creates a GitHub issue if any scanner found issues.

### Reusable Docker Build Workflow

- `on: workflow_call` with inputs: `image_name` (required string), `tag` (required string), `dockerfile_path` (string, default `./Dockerfile`), `build_args` (string, optional).
- Outputs: `image_digest`, `image_uri`.
- Steps: checkout, setup Docker Buildx, login to GHCR using `GITHUB_TOKEN`, cache Docker layers (`actions/cache` or buildx cache), build and push with `docker/build-push-action`.
- Image tagged with both the provided tag and `latest`.

### Expected Functionality

- Push to `main` → CI runs lint, test (2 Python versions), then build and push Docker image.
- PR to `main` → CI runs lint and test only (no build).
- `workflow_dispatch` with `environment: production` → build → staging deploy → production deploy (with approval).
- Daily schedule → all 4 security scans run; if pip-audit finds vulnerabilities, the job fails.

## Acceptance Criteria

- All workflow YAML files are syntactically valid GitHub Actions format.
- CI workflow has correct trigger events, matrix strategy, job dependencies, and concurrency groups.
- CD workflow correctly conditionals on the environment input with proper `if` expressions.
- Security scan workflow runs 4 independent scan jobs and a summary report job.
- Reusable workflow defines `workflow_call` inputs/outputs and uses Docker Buildx with caching.
- Secret references use `${{ secrets.* }}` or environment secrets, never hardcoded credentials.
- Tests validate workflow structure, trigger events, job names, and step ordering.
