# Task: Create a Multi-Stage GitLab CI/CD Pipeline with Caching and Multi-Environment Deployment

## Background

The GitLab repository (https://github.com/gitlabhq/gitlabhq) is an open-source DevOps platform. A new example `.gitlab-ci.yml` pipeline configuration is needed for a Node.js web application that demonstrates a multi-stage pipeline (build, test, security scan, deploy), efficient caching, Docker image building, multi-environment deployment (staging, production) with manual approval gates, and reusable job templates using YAML anchors and `extends`.

## Files to Create/Modify

- `examples/ci-demo/.gitlab-ci.yml` (create) — Complete multi-stage GitLab CI pipeline
- `examples/ci-demo/.gitlab/ci/templates.yml` (create) — Reusable job templates using `extends`
- `examples/ci-demo/.gitlab/ci/deploy.yml` (create) — Deployment jobs for staging and production
- `examples/ci-demo/.gitlab/ci/security.yml` (create) — Security scanning jobs (SAST, dependency scan)
- `examples/ci-demo/Dockerfile` (create) — Multi-stage Dockerfile for the application
- `tests/test_gitlab_ci_patterns.py` (create) — Python tests validating the pipeline YAML structure

## Requirements

### Main Pipeline (.gitlab-ci.yml)

- Stages: `build`, `test`, `security`, `deploy-staging`, `deploy-production`
- Global variables: `DOCKER_DRIVER: overlay2`, `DOCKER_TLS_CERTDIR: "/certs"`, `NODE_VERSION: "20"`
- `include` directive pulling in the three partial CI files from `.gitlab/ci/`
- Default `image: node:20`
- Global `cache` with key `${CI_COMMIT_REF_SLUG}` and paths `["node_modules/"]`

### Build Job

- Stage: `build`
- Script: `npm ci`, `npm run build`
- Artifacts: `dist/` directory with `expire_in: 1 hour`
- Cache: key `${CI_COMMIT_REF_SLUG}`, paths `["node_modules/"]`, policy `push` (only push, don't pull)

### Test Jobs

- **Unit tests** (`test:unit`): stage `test`, script `npm ci && npm run test:unit`, coverage regex `/Lines\s*:\s*(\d+\.\d+)%/`, artifacts for Cobertura coverage report at `coverage/cobertura-coverage.xml`
- **Lint** (`test:lint`): stage `test`, script `npm ci && npm run lint`, allow failure `false`
- **Integration tests** (`test:integration`): stage `test`, script `npm ci && npm run test:integration`, services `["postgres:15"]`, variables `POSTGRES_DB: test`, `POSTGRES_USER: test`, `POSTGRES_PASSWORD: test`, `DATABASE_URL: postgresql://test:test@postgres/test`
- All test jobs inherit from `cache` with policy `pull`

### Security Jobs (security.yml)

- **SAST** (`security:sast`): stage `security`, uses `semgrep` to scan `src/` directory, artifacts report as `sast` type, allow failure `true`
- **Dependency scan** (`security:dependencies`): stage `security`, runs `npm audit --audit-level=high`, allow failure `true`
- Both run only on `main` branch and merge requests

### Deployment Jobs (deploy.yml)

- **Deploy Staging** (`deploy:staging`): stage `deploy-staging`, deploys to staging namespace via `kubectl apply`, environment `name: staging, url: https://staging.example.com`, runs only on `main` branch, uses the `.deploy_template` anchor
- **Deploy Production** (`deploy:production`): stage `deploy-production`, deploys to production namespace, environment `name: production, url: https://app.example.com`, `when: manual` (manual approval gate), runs only on `main` branch
- `.deploy_template` (hidden job template): image `bitnami/kubectl:latest`, before_script configures kubectl with `$KUBE_URL` and `$KUBE_TOKEN` variables

### Docker Build

- Job `build:docker` in stage `build`, image `docker:24`, services `["docker:24-dind"]`
- Builds and tags with both `$CI_COMMIT_SHA` and `latest`, pushes to `$CI_REGISTRY_IMAGE`
- Runs only on `main` and `tags`

### Reusable Templates (templates.yml)

- `.node_template`: sets up Node cache and runs `npm ci`
- `.deploy_template`: kubectl configuration template
- `.rules_template`: common rules for branch/MR-based execution

### Dockerfile

- Multi-stage: build stage (node:20-alpine, npm ci, npm run build) → production stage (node:20-alpine, copy dist and node_modules with --production, expose 8080, run node dist/main.js)
- Non-root user, `HEALTHCHECK` instruction

### Expected Functionality

- A push to `main` triggers: build → tests (parallel) → security (parallel) → deploy staging (auto) → deploy production (manual)
- A merge request triggers: build → tests → security, but no deployment
- Docker image is built and pushed on `main` and tags
- Cache key `${CI_COMMIT_REF_SLUG}` isolates caches per branch
- Integration tests can connect to the PostgreSQL service

## Acceptance Criteria

- All YAML files are valid and parseable
- Pipeline stages execute in the correct order: build → test → security → deploy-staging → deploy-production
- Cache configuration uses branch-specific keys with appropriate push/pull policies
- Test jobs run in parallel within the test stage and produce coverage artifacts
- Security jobs run only on main/MR with `allow_failure: true`
- Staging deploys automatically on main; production requires manual approval
- Docker build uses multi-stage Dockerfile and pushes to the registry
- Reusable templates reduce duplication; `extends` and YAML anchors are used correctly
- Tests validate YAML structure, stage ordering, rules, and environment configuration
