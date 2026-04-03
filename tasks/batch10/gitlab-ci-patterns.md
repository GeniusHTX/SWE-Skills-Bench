# Task: Build Multi-Stage CI/CD Pipeline Configuration for GitLab CE

## Background

The GitLab CE repository (`gitlabhq/gitlabhq`) organizes its CI configuration across `.gitlab-ci.yml` at the root and included files under `.gitlab/ci/`. A new microservice component (`webhooks-processor`) is being added to the platform. It needs a complete GitLab CI pipeline configuration with build, test, security scanning, Docker packaging, and multi-environment deployment stages, plus a dynamic child pipeline for database migrations.

## Files to Create/Modify

- `.gitlab/ci/webhooks-processor.gitlab-ci.yml` (new) — Full multi-stage pipeline for the webhooks-processor service with build, test, scan, package, and deploy stages
- `.gitlab/ci/webhooks-processor-migrations.gitlab-ci.yml` (new) — Dynamic child pipeline template for running database migrations before deployment
- `lib/gitlab/ci/templates/webhooks_docker.yml` (new) — Reusable Docker build-and-push job template using YAML anchors
- `tests/test_gitlab_ci_patterns.py` (new) — Unit tests validating YAML structure, stage ordering, caching, and job dependencies

## Requirements

### Main Pipeline — `webhooks-processor.gitlab-ci.yml`

- Define five stages in order: `build`, `test`, `scan`, `package`, `deploy`
- Set pipeline-level variables: `DOCKER_DRIVER: overlay2`, `DOCKER_TLS_CERTDIR: "/certs"`, `SERVICE_NAME: webhooks-processor`, `RUBY_VERSION: "3.2"`
- **Build job** (`build:webhooks`):
  - Stage `build`, image `ruby:${RUBY_VERSION}`
  - Run `bundle install --jobs=$(nproc) --retry 3 --path vendor/bundle`
  - Cache `vendor/bundle` with key `${CI_COMMIT_REF_SLUG}-bundle` and `pull-push` policy
  - Store `vendor/bundle` as artifact expiring in 1 hour
  - Set `timeout-minutes` (via `timeout`) to 15 minutes
- **Test jobs**:
  - `test:unit` — Stage `test`, `needs: [build:webhooks]`, run `bundle exec rspec spec/services/webhooks_processor/ --format documentation`, coverage regex `/Lines\s*:\s*(\d+\.\d+)%/`, produce Cobertura artifact at `coverage/cobertura.xml`
  - `test:integration` — Stage `test`, `needs: [build:webhooks]`, run `bundle exec rspec spec/integration/webhooks_processor/`, tagged with `allow_failure: true`
  - Both test jobs must use the same cache key as the build job with `pull` policy
- **Security scan job** (`scan:dependencies`):
  - Stage `scan`, use `include` to pull in `Security/Dependency-Scanning.gitlab-ci.yml` and `Security/SAST.gitlab-ci.yml` templates
  - Add a custom `trivy-scan` job using image `aquasec/trivy:latest` that scans `$CI_REGISTRY_IMAGE:$CI_COMMIT_SHA` with `--exit-code 1 --severity HIGH,CRITICAL` and `allow_failure: true`
- **Package job** (`package:docker`):
  - Stage `package`, image `docker:24`, services `docker:24-dind`
  - Log in to `$CI_REGISTRY` using `$CI_REGISTRY_USER` and `$CI_REGISTRY_PASSWORD`
  - Build and push two tags: `$CI_REGISTRY_IMAGE/$SERVICE_NAME:$CI_COMMIT_SHA` and `$CI_REGISTRY_IMAGE/$SERVICE_NAME:latest`
  - Run only on `main` branch and tags
  - Use `cache-from` pointing to the `latest` tag for layer caching
- **Deploy jobs**:
  - `deploy:staging` — Stage `deploy`, `needs: [package:docker]`, environment `staging` with URL `https://staging.gitlab.example.com`, run `kubectl apply -f k8s/staging/` and `kubectl rollout status deployment/$SERVICE_NAME -n staging`, triggered only on `main` branch
  - `deploy:production` — Stage `deploy`, `needs: [package:docker, deploy:staging]`, environment `production` with URL `https://gitlab.example.com`, `when: manual`, triggered only on tags matching `v*`

### Migration Child Pipeline — `webhooks-processor-migrations.gitlab-ci.yml`

- Define two stages: `migrate` and `verify`
- `migrate:run` job: image `ruby:${RUBY_VERSION}`, run `bundle exec rake db:migrate RAILS_ENV=$DEPLOY_ENV`
- `migrate:verify` job: `needs: [migrate:run]`, run `bundle exec rake db:migrate:status RAILS_ENV=$DEPLOY_ENV` and verify no pending migrations
- The main pipeline's `deploy:staging` job must trigger this child pipeline using `trigger.include` with `artifact` strategy

### Reusable Docker Template — `webhooks_docker.yml`

- Define a YAML anchor `&docker_build` containing the `image`, `services`, `before_script` (registry login), and `script` (build and push) steps
- The anchor must accept variables `$IMAGE_TAG` and `$DOCKERFILE_PATH` for flexibility
- `package:docker` in the main pipeline must reference this template via `<<: *docker_build`

### Caching Strategy

- `vendor/bundle` cache key must be `${CI_COMMIT_REF_SLUG}-bundle`
- Build job uses `pull-push` policy; test jobs use `pull` policy
- A fallback cache key `${CI_DEFAULT_BRANCH}-bundle` must be set for branch pipelines

### Expected Functionality

- Push to `main` branch → stages run in order: build → test (unit + integration parallel) → scan → package → deploy:staging
- Push to `develop` branch → build and test stages run; package and deploy do not execute
- Push tag `v1.2.3` → build → test → scan → package → deploy:production (manual gate)
- `test:integration` failure → pipeline continues (allowed failure); `test:unit` failure → pipeline stops
- Subsequent pipeline on same branch → `vendor/bundle` cache hit, `bundle install` completes faster
- `trivy-scan` finds CRITICAL vulnerability → job fails but pipeline continues
- `deploy:staging` triggers migration child pipeline before applying Kubernetes manifests

## Acceptance Criteria

- `.gitlab/ci/webhooks-processor.gitlab-ci.yml` defines exactly five stages in the correct order and all specified jobs
- Build job caches `vendor/bundle` with `pull-push` policy; test jobs use `pull` policy with the same cache key
- `package:docker` job logs into the registry using CI variables, builds and pushes two tags, and restricts execution to `main` and tags
- `deploy:production` requires manual approval (`when: manual`) and runs only on version tags
- Security scanning includes both GitLab templates and a custom Trivy scan
- `webhooks-processor-migrations.gitlab-ci.yml` defines a migrate-then-verify pipeline triggered as a child from the main pipeline
- `webhooks_docker.yml` defines a reusable YAML anchor for Docker build steps
- No job contains hardcoded credentials; all secrets use `$CI_REGISTRY_PASSWORD`, `$KUBE_TOKEN`, etc.
- Tests in `tests/test_gitlab_ci_patterns.py` pass, validating YAML structure and job configuration
