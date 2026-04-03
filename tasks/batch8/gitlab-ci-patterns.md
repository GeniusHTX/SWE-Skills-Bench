# Task: Build a Multi-Stage GitLab CI Pipeline Generator for GitLab

## Background

GitLab (https://github.com/gitlabhq/gitlabhq) is a DevOps platform with integrated CI/CD. The project needs a Python utility that generates GitLab CI pipeline configurations (`.gitlab-ci.yml`) for multi-stage build/test/deploy workflows. The generator must produce valid GitLab CI YAML with proper stage ordering, job dependencies, caching strategies, artifact management, environment-based deployment gates, and Docker-in-Docker build support.

## Files to Create/Modify

- `scripts/ci/pipeline_generator.py` (create) — `PipelineGenerator` class that constructs GitLab CI pipeline YAML from a declarative project configuration, supporting build, test, security scan, and deploy stages
- `scripts/ci/job_templates.py` (create) — `JobTemplate` base class and concrete templates: `BuildJob`, `TestJob`, `LintJob`, `SecurityScanJob`, `DockerBuildJob`, `DeployJob`, each producing a valid GitLab CI job dict
- `scripts/ci/cache_config.py` (create) — `CacheStrategy` class managing cache key generation, path configuration, and policy (pull, push, pull-push) based on job type and branch
- `scripts/ci/validator.py` (create) — `PipelineValidator` class checking generated pipeline YAML for common errors: circular dependencies, missing stage references, invalid `only/except` rules, and missing required variables
- `tests/test_gitlab_ci_patterns.py` (create) — Tests for pipeline generation, job template rendering, cache configuration, and validation logic

## Requirements

### PipelineGenerator

- Constructor: `PipelineGenerator(project_name: str, language: str, deploy_targets: list[str] = None)`
- `language` is one of `"python"`, `"node"`, `"ruby"`, `"go"`
- `generate() -> dict` — Produce the complete pipeline dict that serializes to valid `.gitlab-ci.yml`:
  - Top-level keys: `stages`, `variables`, `default` (with `image`, `cache`), plus individual job definitions
  - Stage order: `[".pre", "build", "test", "security", "package", "deploy-staging", "deploy-production", ".post"]`
- `add_job(name: str, job: dict) -> None` — Add a custom job definition
- `set_variables(variables: dict) -> None` — Set top-level pipeline variables
- `to_yaml() -> str` — Serialize the pipeline to YAML string using `yaml.dump` with `default_flow_style=False`
- `to_dict() -> dict` — Return the raw pipeline dictionary

### Job Templates

- `BuildJob(language: str)`:
  - Python: `pip install -r requirements.txt && python setup.py build`
  - Node: `npm ci && npm run build`
  - Ruby: `bundle install && bundle exec rake build`
  - Go: `go build ./...`
  - Produces artifacts at `dist/` (or equivalent) with 1-hour expiry
- `TestJob(language: str, coverage_regex: str = None)`:
  - Runs language-appropriate test command with coverage
  - Sets `coverage` keyword with appropriate regex pattern
  - Produces JUnit report artifact at `report.xml`
  - `allow_failure: false`
- `SecurityScanJob()`:
  - Uses `gitleaks/gitleaks` image for secret scanning
  - Produces SAST report artifact
  - `allow_failure: true` (advisory only)
- `DockerBuildJob(image_name: str, registry: str = "$CI_REGISTRY")`:
  - Uses `docker:24-dind` service
  - Login to registry, build with `--cache-from`, push with `$CI_COMMIT_TAG` and `latest` tags
  - Only runs on tags matching `v*`
- `DeployJob(environment: str, namespace: str)`:
  - For staging: automatic trigger on `main` branch
  - For production: `when: manual` with `allow_failure: false`
  - Uses `kubectl set image` with the built Docker image tag
  - Defines `environment:` with `name` and `url`
  - Runs `kubectl rollout status` after deployment

### CacheStrategy

- `CacheStrategy(language: str)`:
  - Python: cache `venv/` and `.pip/` with key `pip-$CI_COMMIT_REF_SLUG`
  - Node: cache `node_modules/` with key from lockfile hash `node-${CI_COMMIT_REF_SLUG}-$CI_JOB_IMAGE`
  - Ruby: cache `vendor/ruby/` with key `ruby-$CI_COMMIT_REF_SLUG`
  - Go: cache `$GOPATH/pkg/mod/` with key `go-$CI_COMMIT_REF_SLUG`
- `for_job(job_type: str) -> dict` — Return cache dict with appropriate `policy`:
  - `"build"`: `policy: pull-push` (populate cache)
  - `"test"`: `policy: pull` (read-only)
  - `"deploy"`: no cache

### PipelineValidator

- `validate(pipeline: dict) -> list[str]` — Return a list of error strings (empty = valid):
  - Jobs referencing undefined stages: `"Job '{name}' references undefined stage '{stage}'"`
  - Jobs with `needs:` referencing non-existent jobs: `"Job '{name}' needs non-existent job '{dep}'"`
  - Deploy jobs without `environment:` key: `"Deploy job '{name}' missing 'environment' configuration"`
  - Jobs using `only/except` with `rules:` (mutually exclusive): `"Job '{name}' cannot use both 'only/except' and 'rules'"`
  - Missing `$CI_REGISTRY_IMAGE` variable in Docker build jobs
- `validate_yaml(yaml_string: str) -> list[str]` — Parse YAML and run validation

### Edge Cases

- `deploy_targets` is empty: no deploy stages or jobs generated
- Unknown language: raise `ValueError("Unsupported language: {language}")`
- Custom job with stage not in the default stage list: auto-add the stage in correct position
- Duplicate job names: raise `ValueError("Duplicate job name: {name}")`

## Expected Functionality

- `PipelineGenerator("myapp", "python", ["staging", "production"]).generate()` produces a complete pipeline with build, test, security scan, Docker build, and two deploy jobs
- The generated YAML is valid GitLab CI syntax with proper stage ordering and job dependencies
- Docker build job only triggers on version tags, staging deploys automatically on main, production requires manual approval
- `PipelineValidator` catches a job referencing a non-existent stage and returns a descriptive error

## Acceptance Criteria

- `PipelineGenerator` produces valid GitLab CI pipeline dictionaries for Python, Node, Ruby, and Go projects
- Job templates generate correct scripts, artifacts, and rules for each job type
- Cache configuration uses language-appropriate paths and keys with correct policies per job type
- Deploy jobs distinguish staging (automatic) from production (manual) with proper environment configuration
- `PipelineValidator` detects undefined stages, missing dependencies, and invalid rule combinations
- Generated YAML is parseable and structurally valid
- All tests pass with `pytest`
