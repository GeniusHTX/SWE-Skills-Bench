# Task: Implement Multi-Stage GitLab CI Pipeline with Security Scanning

## Background

GitLab (https://github.com/gitlabhq/gitlabhq) is a DevOps platform with built-in CI/CD. The project needs a comprehensive `.gitlab-ci.yml` pipeline configuration that demonstrates multi-stage builds, Docker image building, security scanning integration, dynamic child pipelines, and environment-specific deployments.

## Files to Create/Modify

- `.gitlab-ci.yml` (create) — Root pipeline configuration with stages, global variables, and includes
- `ci/templates/build.yml` (create) — Build stage template with Docker multi-stage build
- `ci/templates/test.yml` (create) — Test stage template with parallel test execution and coverage
- `ci/templates/security.yml` (create) — Security scanning stage (SAST, dependency scanning, container scanning)
- `ci/templates/deploy.yml` (create) — Deployment stage template with environment-specific configurations
- `ci/dynamic/generate-pipeline.rb` (create) — Script to generate dynamic child pipelines based on changed files

## Requirements

### Pipeline Stages

- Define stages in order: `build`, `test`, `security`, `deploy-staging`, `deploy-production`
- Global variables: `DOCKER_REGISTRY` (registry URL), `IMAGE_TAG` (default: `$CI_COMMIT_SHORT_SHA`), `RUBY_VERSION` (default: `3.2`)
- Global cache: cache `vendor/` and `node_modules/` directories keyed by lockfile hashes
- Include templates using `include: local` referencing files under `ci/templates/`

### Build Stage

- `build:docker` job: build a Docker image using multi-stage Dockerfile
  - Use Docker-in-Docker (`docker:24-dind`) as the service
  - Build with `--build-arg RUBY_VERSION=$RUBY_VERSION`
  - Tag with both `$CI_COMMIT_SHORT_SHA` and `latest` (only for default branch)
  - Push to `$DOCKER_REGISTRY`
  - Only run when files in `app/`, `lib/`, `config/`, or `Gemfile*` change (using `rules: changes`)
- `build:assets` job: compile frontend assets
  - Run `yarn install --frozen-lockfile` and `yarn build`
  - Cache `node_modules/` keyed by `yarn.lock` hash
  - Upload `public/assets/` as artifacts (expire in 1 week)

### Test Stage

- `test:rspec` job: run Ruby tests with parallel execution
  - Use `parallel: 4` to split tests across 4 runners
  - Use `--format documentation --format RspecJunitFormatter` for JUnit XML output
  - Upload JUnit XML as artifact for test report visualization
  - Coverage regex: `/\(\d+\.\d+%\) covered/`
  - `needs: ["build:docker"]` — depends on the build stage
- `test:jest` job: run JavaScript tests
  - Run `yarn test --coverage`
  - Upload coverage report as artifact
  - `allow_failure: false`

### Security Scanning

- `security:sast` job: Static Application Security Testing
  - Use GitLab's SAST template (`Security/SAST.gitlab-ci.yml`)
  - Configure `SAST_EXCLUDED_PATHS` to skip `spec/`, `test/`, `vendor/`
- `security:dependency-scanning` job: Dependency vulnerability scanning
  - Use GitLab's Dependency Scanning template
  - Only run on merge requests and the default branch
- `security:container-scanning` job: Scan the built Docker image
  - Use `$DOCKER_REGISTRY/$CI_PROJECT_PATH:$CI_COMMIT_SHORT_SHA` as the image to scan
  - `needs: ["build:docker"]`

### Deployment

- `deploy:staging` job:
  - Stage: `deploy-staging`
  - Environment: `staging` with URL `https://staging.example.com`
  - Run deployment script referencing the built Docker image
  - Only run on the default branch
  - `when: on_success` (auto-deploy to staging)
- `deploy:production` job:
  - Stage: `deploy-production`
  - Environment: `production` with URL `https://app.example.com`
  - `when: manual` (require manual approval)
  - `needs: ["deploy:staging"]` — can only deploy to prod after staging
  - Only run on tags matching `v*`
  - `allow_failure: false`

### Dynamic Child Pipeline

- `generate-pipeline` job in the build stage runs `ci/dynamic/generate-pipeline.rb`
- The script checks which files changed (via `CI_MERGE_REQUEST_DIFF_BASE_SHA`) and generates a child pipeline YAML that only includes relevant jobs
- If only `docs/` files changed, the generated pipeline runs only a `lint:docs` job
- If only `spec/` files changed, the generated pipeline runs only test jobs
- The generated YAML is saved as an artifact and triggered via `trigger: strategy: depend`

### Expected Functionality

- A push to the default branch that changes `app/models/user.rb` triggers: build:docker → test:rspec (parallel 4) → security scans → deploy:staging
- A merge request changing only `doc/api/users.md` triggers only the dynamic pipeline with `lint:docs`
- A tag `v1.2.3` triggers the full pipeline including `deploy:production` (manual gate)
- `test:rspec` produces JUnit XML artifacts visible in the merge request
- The Docker image is only rebuilt when source files change, not when only docs change

## Acceptance Criteria

- Pipeline defines 5 stages in the correct order with proper job dependencies using `needs`
- Docker build uses multi-stage building, conditional tagging, and only triggers on source file changes
- Test jobs use parallel execution for rspec and produce JUnit XML / coverage artifacts
- Security scanning includes SAST, dependency scanning, and container scanning with correct configuration
- Staging deploys automatically on default branch pushes; production requires manual approval and only runs on version tags
- Dynamic child pipeline generation script produces valid YAML based on changed files
- Global cache configuration uses lockfile-based keys for Ruby and Node.js dependencies
- All CI templates use `include: local` for modular organization
