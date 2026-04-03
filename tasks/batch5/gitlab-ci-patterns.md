# Task: Configure GitLab CI/CD Pipelines for a Rails Application

## Background

GitLab (https://github.com/gitlabhq/gitlabhq) is a DevOps platform with built-in CI/CD. This task requires creating a `.gitlab-ci.yml` configuration for a Rails application with multi-stage pipelines, caching strategies, parallel testing, environment-specific deployments, and a manual rollback mechanism.

## Files to Create/Modify

- `.gitlab-ci.yml` (create) — Main pipeline configuration with stages: prepare, test, build, deploy, rollback.
- `ci/templates/test-template.yml` (create) — Reusable job template for running different test suites (unit, integration, system) with shared setup.
- `ci/templates/deploy-template.yml` (create) — Reusable deployment template with environment configuration, Kubernetes deployment, and health check verification.
- `ci/scripts/rollback.sh` (create) — Shell script for manual rollback: reverts Kubernetes deployment to the previous revision and verifies rollout status.
- `tests/test_gitlab_ci_patterns.py` (create) — Tests verifying YAML structure, stage ordering, cache configuration, and rule expressions.

## Requirements

### Pipeline Stages

- `prepare` → `test` → `build` → `deploy` → `rollback` (manual).

### Prepare Stage

- **Job: bundle-install** — Install Ruby gems with `bundle install --jobs=4 --retry=3 --path vendor/bundle`.
- Cache: key `gems-$CI_COMMIT_REF_SLUG`, paths `vendor/bundle/`. Policy: `pull-push`.
- Artifacts: `vendor/bundle/` (expire in 1 hour).

### Test Stage (using template)

- **Job: unit-tests** — Extends `.test-template`. Runs `bundle exec rspec spec/models spec/services --format progress --format RspecJunitFormatter -o rspec_unit.xml`.  Parallel: 4 (uses `CI_NODE_INDEX` and `CI_NODE_TOTAL` for test splitting with `parallel_tests` gem).
- **Job: integration-tests** — Extends `.test-template`. Runs `bundle exec rspec spec/requests --format progress`. Services: `postgres:15` and `redis:7`. Variables: `DATABASE_URL`, `REDIS_URL`.
- **Job: lint** — `bundle exec rubocop --format json --out rubocop.json`. Allow failure: true.
- **Test template** (`.test-template`): sets up Ruby 3.2 image, restores gem cache, runs `bundle exec rails db:create db:schema:load`, defines `junit` report artifacts.
- Coverage: `unit-tests` collects coverage via `SimpleCov` with regex `Line Coverage: (\d+\.\d+)%`.

### Build Stage

- **Job: docker-build** — builds Docker image using Kaniko, pushes to GitLab registry. Tags with `$CI_COMMIT_SHORT_SHA` and branch name. Only runs on `main` and tags.
- Registry: `$CI_REGISTRY_IMAGE`.
- Cache from: previous image for layer caching.

### Deploy Stage

- **Job: deploy-staging** — Extends `.deploy-template`. Environment: `staging`, URL `https://staging.example.com`. Auto-deploys on `main` branch.
- **Job: deploy-production** — Extends `.deploy-template`. Environment: `production`, URL `https://example.com`. Only on tags matching `v*`. `when: manual`. Requires `deploy-staging` to pass first (via `needs`).
- **Deploy template** (`.deploy-template`): uses `kubectl set image`, waits for rollout with `kubectl rollout status --timeout=300s`, runs smoke test (`curl -sf $ENVIRONMENT_URL/health`).

### Rollback Stage

- **Job: rollback-production** — `when: manual`. Script: executes `ci/scripts/rollback.sh` which runs `kubectl rollout undo deployment/webapp` and `kubectl rollout status --timeout=120s`. Only available on `main` branch.

### Rules and Conditions

- All test jobs run on merge requests and `main` branch.
- Build jobs run only on `main` and tags.
- Deploy to staging only on `main`.
- Deploy to production only on tags matching `v[0-9]+.*`.
- Rollback only on `main`, requires manual trigger.

### Expected Functionality

- Push to feature branch → prepare + test stages run (lint, unit, integration).
- Merge to main → test + build + deploy-staging.
- Push tag `v1.2.3` → test + build + deploy-staging (auto) + deploy-production (manual gate).
- Click rollback button → reverts production to previous version, verifies rollout.

## Acceptance Criteria

- `.gitlab-ci.yml` defines all 5 stages and all jobs with correct ordering.
- Reusable templates (`.test-template`, `.deploy-template`) are used via `extends`.
- Caching is configured for gems with correct key, paths, and policy.
- Parallel testing distributes across 4 nodes with JUnit report collection.
- Build uses Kaniko for Docker-in-Docker-free image building.
- Deployment jobs correctly target environments with URLs and conditions.
- Rollback script handles `kubectl rollout undo` with status verification.
- Tests validate stage order, job names, rule expressions, and cache configuration.
