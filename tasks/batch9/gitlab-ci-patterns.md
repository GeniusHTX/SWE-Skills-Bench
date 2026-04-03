# Task: Create a Multi-Stage GitLab CI Pipeline for a Ruby on Rails Application

## Background

GitLab (https://github.com/gitlabhq/gitlabhq) provides CI/CD via `.gitlab-ci.yml`. A comprehensive GitLab CI pipeline configuration is needed for a Ruby on Rails application with multi-stage workflows, Docker-in-Docker builds, review environments, caching strategies, database testing, security scanning, and multi-environment deployments with manual approval gates.

## Files to Create/Modify

- `.gitlab-ci.yml` (create) — Main pipeline configuration with stages, global variables, include references, and workflow rules
- `.gitlab/ci/build.gitlab-ci.yml` (create) — Build stage: Docker image build and push to GitLab Container Registry using kaniko
- `.gitlab/ci/test.gitlab-ci.yml` (create) — Test stage: RSpec tests with PostgreSQL service, parallel test splitting, coverage reporting with Cobertura
- `.gitlab/ci/lint.gitlab-ci.yml` (create) — Lint stage: RuboCop, Brakeman security scanner, bundler-audit dependency check
- `.gitlab/ci/deploy.gitlab-ci.yml` (create) — Deploy stage: review environments, staging auto-deploy, production manual deploy with Kubernetes
- `.gitlab/ci/templates.gitlab-ci.yml` (create) — Reusable job templates using YAML anchors and `extends` for common patterns
- `scripts/ci/split_tests.rb` (create) — Ruby script that splits RSpec test files into N parallel groups by file duration from previous runs

## Requirements

### Main Pipeline (`.gitlab-ci.yml`)

- `stages:` — `[".pre", "build", "test", "lint", "security", "deploy", "cleanup"]`
- `workflow.rules`:
  - Run on merge requests
  - Run on default branch (main)
  - Run on tags matching `v*`
  - Skip when commit message contains `[ci skip]`
- `variables`:
  - `DOCKER_IMAGE: $CI_REGISTRY_IMAGE:$CI_COMMIT_SHA`
  - `POSTGRES_DB: test_db`
  - `POSTGRES_USER: runner`
  - `POSTGRES_PASSWORD: password`
  - `BUNDLE_CACHE_PATH: vendor/bundle`
  - `RAILS_ENV: test`
- `include:` — references to all `.gitlab/ci/*.gitlab-ci.yml` files using `local:` paths
- `default.cache`:
  - `key: "${CI_COMMIT_REF_SLUG}-gems"`
  - `paths: ["vendor/bundle/"]`
  - `policy: pull`

### Build Stage (`.gitlab/ci/build.gitlab-ci.yml`)

- Job `build-image`:
  - `stage: build`
  - `image: gcr.io/kaniko-project/executor:v1.18.0-debug` (not Docker-in-Docker for security)
  - `script`: kaniko build pushing to `$CI_REGISTRY_IMAGE:$CI_COMMIT_SHA` and `$CI_REGISTRY_IMAGE:latest` (on default branch)
  - `before_script`: create `/kaniko/.docker/config.json` with registry credentials from `$CI_REGISTRY_USER` and `$CI_REGISTRY_PASSWORD`
  - `rules: [{if: '$CI_PIPELINE_SOURCE == "merge_request_event"'}, {if: '$CI_COMMIT_BRANCH == $CI_DEFAULT_BRANCH'}]`
- Job `bundle-install`:
  - `stage: .pre`
  - `image: ruby:3.2`
  - `script: ["bundle config set --local path vendor/bundle", "bundle install --jobs=4"]`
  - `cache.policy: pull-push` (this job populates the cache)

### Test Stage (`.gitlab/ci/test.gitlab-ci.yml`)

- Job `rspec`:
  - `stage: test`
  - `image: ruby:3.2`
  - `services: [{name: "postgres:15", alias: "db"}]`
  - `parallel: 4` — Run 4 parallel test jobs
  - `before_script`: `["bundle config set --local path vendor/bundle", "bundle install", "bundle exec rails db:create db:schema:load"]`
  - `script: ["ruby scripts/ci/split_tests.rb $CI_NODE_INDEX $CI_NODE_TOTAL | xargs bundle exec rspec --format progress --format RspecJunitFormatter --out rspec_results.xml"]`
  - `artifacts.reports.junit: rspec_results.xml`
  - `artifacts.reports.coverage_report.coverage_format: cobertura`
  - `artifacts.reports.coverage_report.path: coverage/coverage.xml`
  - `coverage: '/Lines\s*:\s*(\d+\.\d+)%/'`
  - `needs: ["bundle-install"]`

### Lint Stage (`.gitlab/ci/lint.gitlab-ci.yml`)

- Job `rubocop`:
  - `stage: lint`
  - `script: ["bundle exec rubocop --parallel --format json --out rubocop_report.json || true", "bundle exec rubocop --parallel"]`
  - `artifacts.paths: ["rubocop_report.json"]`
  - `allow_failure: true`
- Job `brakeman`:
  - `stage: security`
  - `script: ["bundle exec brakeman -o brakeman_report.json -o brakeman_report.html"]`
  - `artifacts.paths: ["brakeman_report.json", "brakeman_report.html"]`
  - `artifacts.when: always`
- Job `bundler-audit`:
  - `stage: security`
  - `script: ["bundle exec bundler-audit check --update"]`

### Deploy Stage (`.gitlab/ci/deploy.gitlab-ci.yml`)

- Job `deploy-review`:
  - `stage: deploy`
  - `environment.name: "review/$CI_COMMIT_REF_SLUG"`
  - `environment.url: "https://$CI_COMMIT_REF_SLUG.review.example.com"`
  - `environment.on_stop: stop-review`
  - `environment.auto_stop_in: "1 week"`
  - `script`: kubectl apply with namespace per review environment
  - `rules: [{if: '$CI_PIPELINE_SOURCE == "merge_request_event"'}]`
- Job `stop-review`:
  - `stage: cleanup`
  - `environment.name: "review/$CI_COMMIT_REF_SLUG"`
  - `environment.action: stop`
  - `when: manual`
  - `script`: kubectl delete namespace
- Job `deploy-staging`:
  - `stage: deploy`
  - `environment.name: staging`
  - `script`: kubectl set image with `$DOCKER_IMAGE`
  - `rules: [{if: '$CI_COMMIT_BRANCH == $CI_DEFAULT_BRANCH'}]`
- Job `deploy-production`:
  - `stage: deploy`
  - `environment.name: production`
  - `when: manual`
  - `allow_failure: false`
  - `rules: [{if: '$CI_COMMIT_TAG =~ /^v\d+/'}]`
  - `needs: ["deploy-staging"]`

### Templates (`.gitlab/ci/templates.gitlab-ci.yml`)

- `.ruby-job` template: image `ruby:3.2`, cache config, `before_script` with bundle install
- `.deploy-job` template: image `bitnami/kubectl:latest`, `before_script` configuring kubeconfig from `$KUBE_CONFIG` variable
- `.only-default-branch` rules template
- `.only-merge-request` rules template
- All deploy jobs `extends: .deploy-job`; all Ruby jobs `extends: .ruby-job`

### Test Splitter (`scripts/ci/split_tests.rb`)

- Reads RSpec test files from `spec/` directory
- Accepts `NODE_INDEX` and `NODE_TOTAL` as arguments
- Splits files into `NODE_TOTAL` groups using round-robin on sorted file list
- Outputs file paths for the group matching `NODE_INDEX` (0-based), one per line
- If a timing file (`tmp/rspec_timings.json`) exists, split by total duration per group instead of round-robin

### Expected Functionality

- Pipeline runs 7 stages in order with proper dependency chains
- `rspec` job runs 4 parallel instances, each testing a different file subset
- Review environments are created per merge request and auto-stop after 1 week
- Production deploy requires manual approval and only runs on version tags
- Cache is populated by `bundle-install` in `.pre` stage and consumed by subsequent jobs

## Acceptance Criteria

- `.gitlab-ci.yml` defines valid pipeline stages and workflow rules
- Build uses kaniko (not Docker-in-Docker) for security
- Test jobs run in parallel with proper PostgreSQL service and JUnit/Cobertura artifacts
- Security scanning includes both Brakeman and bundler-audit
- Deploy jobs use proper environment configuration with review/staging/production separation
- Production deploy is manual with needs dependency on staging
- Templates reduce duplication using `extends`
- Test splitter correctly distributes files across N nodes
- `python -m pytest /workspace/tests/test_gitlab_ci_patterns.py -v --tb=short` passes
