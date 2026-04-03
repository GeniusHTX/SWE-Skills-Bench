# Task: Build a GitLab CI/CD Pipeline for a Python Microservice with Multi-Environment Deployment

## Background

A Python microservice (FastAPI) needs a complete GitLab CI/CD pipeline with stages for linting, testing, building a Docker image, and deploying to staging and production Kubernetes clusters. The pipeline must use GitLab's caching for pip dependencies, produce Cobertura coverage reports, implement YAML anchors for DRY configuration, and support Terraform for infrastructure provisioning.

## Files to Create/Modify

- `.gitlab-ci.yml` (create) — Main pipeline definition with 5 stages: validate, test, build, deploy-staging, deploy-production
- `ci/templates/python.yml` (create) — Reusable YAML template for Python job configuration (image, cache, before_script)
- `ci/templates/deploy.yml` (create) — Reusable deploy template with kubectl configuration
- `ci/templates/terraform.yml` (create) — Terraform validate/plan/apply template for infrastructure changes
- `Dockerfile` (create) — Multi-stage Dockerfile for the FastAPI service

## Requirements

### Main Pipeline (`.gitlab-ci.yml`)

- Stages: `validate`, `test`, `build`, `deploy-staging`, `deploy-production`.
- Include templates: `ci/templates/python.yml`, `ci/templates/deploy.yml`, `ci/templates/terraform.yml`.
- Variables:
  - `DOCKER_DRIVER: overlay2`
  - `DOCKER_TLS_CERTDIR: "/certs"`
  - `PYTHON_VERSION: "3.12"`
  - `PIP_CACHE_DIR: "$CI_PROJECT_DIR/.pip-cache"`

#### validate stage

- **lint** job — extends `.python-base`, runs `ruff check src/ tests/` and `ruff format --check src/ tests/`. Rules: runs on merge requests and default branch.
- **type-check** job — extends `.python-base`, runs `mypy src/ --strict`. Allow failure: `true`.

#### test stage

- **unit-test** job — extends `.python-base`, runs `pytest tests/unit/ --cov=src --cov-report=xml:coverage.xml --cov-report=term -v`. Artifacts: Cobertura coverage report (`coverage_report: { coverage_format: cobertura, path: coverage.xml }`). Coverage regex: `'/TOTAL.*\s(\d+\.\d+)%/'`. Parallel: 3 (using `--splits` for pytest-split).
- **integration-test** job — extends `.python-base`, uses `services:` for PostgreSQL (`postgres:16`) and Redis (`redis:7`). Variables: `POSTGRES_DB: testdb`, `POSTGRES_USER: test`, `POSTGRES_PASSWORD: test`, `DATABASE_URL: postgresql://test:test@postgres:5432/testdb`, `REDIS_URL: redis://redis:6379`. Runs `pytest tests/integration/ -v`. Rules: runs on merge requests and default branch.

#### build stage

- **build-docker** job — image `docker:24` with `docker:24-dind` service. Logs into `$CI_REGISTRY`. Builds and pushes `$CI_REGISTRY_IMAGE:$CI_COMMIT_SHA` and `$CI_REGISTRY_IMAGE:latest`. Uses `--cache-from $CI_REGISTRY_IMAGE:latest` for layer caching. Rules: only on default branch and tags.

#### deploy-staging stage

- **deploy-staging** job — extends `.deploy-base`. Runs `kubectl apply -f k8s/ -n staging` then `kubectl set image deployment/api api=$CI_REGISTRY_IMAGE:$CI_COMMIT_SHA -n staging` then `kubectl rollout status deployment/api -n staging --timeout=180s`. Environment: `name: staging, url: https://staging-api.example.com`. Rules: only on default branch. Runs automatically.

#### deploy-production stage

- **deploy-production** job — extends `.deploy-base`. Same kubectl pattern but namespace `production`. Environment: `name: production, url: https://api.example.com`. Rules: only on default branch. `when: manual` with `allow_failure: false` (blocking).

### Python Template (`ci/templates/python.yml`)

- `.python-base` hidden job:
  - Image: `python:${PYTHON_VERSION}`
  - Cache: key `${CI_COMMIT_REF_SLUG}-pip`, paths `[".pip-cache/"]`, policy `pull-push`
  - Before_script: `pip install --cache-dir $PIP_CACHE_DIR -r requirements.txt -r requirements-dev.txt`

### Deploy Template (`ci/templates/deploy.yml`)

- `.deploy-base` hidden job:
  - Image: `bitnami/kubectl:1.29`
  - Before_script: configure kubectl using `$KUBE_URL` and `$KUBE_TOKEN` CI variables (set cluster, credentials, context).
  - After_script: log deployment result (`kubectl get deployment/api -n $KUBE_NAMESPACE -o wide`).

### Terraform Template (`ci/templates/terraform.yml`)

- `.terraform-base` hidden job with image `hashicorp/terraform:1.6`.
- **tf-validate** job (validate stage): `terraform init -backend=false && terraform validate`.
- **tf-plan** job (test stage): `terraform init && terraform plan -out=plan.tfplan`. Artifact: `plan.tfplan`, expire in 1 hour. Rules: changes to `terraform/**`.
- **tf-apply** job (deploy-staging stage): `terraform init && terraform apply plan.tfplan`. When: manual. Dependencies: `tf-plan`. Rules: only default branch, changes to `terraform/**`.

### Dockerfile

- Stage 1 (`builder`): `python:3.12-slim`, copy `requirements.txt`, install dependencies to `/install`, copy source.
- Stage 2 (`runtime`): `python:3.12-slim`, copy `--from=builder /install`, copy source, create non-root user `appuser`, expose port 8000, run with `uvicorn src.main:app --host 0.0.0.0 --port 8000`.

### Expected Functionality

- Merge request opened → `lint`, `type-check`, `unit-test`, `integration-test` jobs run.
- Push to main → all stages run through `deploy-staging` automatically; `deploy-production` waits for manual click.
- Tag pushed → `build-docker` runs, images tagged with commit SHA.
- Changes in `terraform/` directory → `tf-validate`, `tf-plan` run; `tf-apply` available as manual job.
- Parallel unit tests split across 3 runners.
- PostgreSQL and Redis services available during integration tests.

## Acceptance Criteria

- Pipeline has 5 stages with correct job-to-stage mapping and dependency ordering.
- Python jobs reuse `.python-base` template with pip caching keyed by branch slug.
- Unit tests produce Cobertura XML coverage report and extract coverage percentage via regex.
- Integration tests have PostgreSQL 16 and Redis 7 as services with correct connection variables.
- Docker build uses layer caching from the latest image and pushes SHA-tagged images.
- Deploy jobs reuse `.deploy-base` template with kubectl configured from CI variables.
- Production deploy is manual with blocking (`allow_failure: false`).
- Terraform jobs run conditionally on changes to `terraform/` directory.
- YAML anchors or `extends:` eliminate configuration duplication across jobs.
