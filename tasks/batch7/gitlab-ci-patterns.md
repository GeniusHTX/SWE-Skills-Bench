# Task: Add a Reusable Multi-Stage Pipeline Template to GitLab CI

## Background

The GitLab CI codebase (https://github.com/gitlabhq/gitlabhq) includes Ruby-based pipeline configuration generators and helpers. The task is to implement a reusable `.gitlab-ci.yml` pipeline configuration class in Ruby that generates a multi-stage CI pipeline with parallel test splitting, Docker image caching, and conditional deployment to Kubernetes based on branch name and environment variables.

## Files to Create/Modify

- `lib/gitlab/ci/pipeline_template_generator.rb` (create) — `PipelineTemplateGenerator` class that generates a complete `.gitlab-ci.yml` configuration hash for a given project type
- `lib/gitlab/ci/stage_definitions.rb` (create) — Stage and job definition structs used by the generator
- `spec/lib/gitlab/ci/pipeline_template_generator_spec.rb` (create) — RSpec unit tests for the generator

## Requirements

### `StageDefinitions` (`stage_definitions.rb`)

```ruby
module Gitlab
  module CI
    StageConfig = Struct.new(:name, :parallel, :allow_failure, keyword_init: true)
    
    JobDefinition = Struct.new(
      :name, :stage, :image, :script, :artifacts, 
      :cache, :only, :except, :needs, :parallel,
      keyword_init: true
    )
  end
end
```

### `PipelineTemplateGenerator` (`pipeline_template_generator.rb`)

```ruby
module Gitlab
  module CI
    class PipelineTemplateGenerator
      SUPPORTED_TYPES = %w[rails node python golang].freeze
      DEFAULT_TEST_PARALLELISM = 4

      def initialize(project_type:, deploy_environments: %w[staging production], parallel_tests: DEFAULT_TEST_PARALLELISM)
        # validate project_type against SUPPORTED_TYPES
        # store config
      end

      def generate
        # Returns a Hash representing the full .gitlab-ci.yml structure
        # Keys: "stages", "variables", "default", and each job name
      end
    end
  end
end
```

#### `generate` Output Structure

The returned Hash must include:

**`stages`** — ordered array: `["build", "test", "security", "deploy"]`

**`variables`** — top-level variables:
```yaml
DOCKER_DRIVER: overlay2
DOCKER_TLS_CERTDIR: "/certs"
DOCKER_REGISTRY: "${CI_REGISTRY}"
IMAGE_TAG: "${CI_REGISTRY_IMAGE}:${CI_COMMIT_REF_SLUG}"
```

**`default`** — default settings applied to all jobs:
```yaml
retry:
  max: 2
  when: runner_system_failure
interruptible: true
tags:
  - docker
```

**`build-image`** job (stage: `build`):
- Image: `docker:24.0`
- Services: `["docker:24.0-dind"]`
- Script:
  1. `docker login -u $CI_REGISTRY_USER -p $CI_REGISTRY_PASSWORD $CI_REGISTRY`
  2. `docker build --cache-from $IMAGE_TAG -t $IMAGE_TAG .`
  3. `docker push $IMAGE_TAG`
- Cache key: `${CI_COMMIT_REF_SLUG}-docker`

**`test`** job (stage: `test`):
- Image: project-specific (e.g., `ruby:3.2` for rails, `node:20` for node, `python:3.11` for python, `golang:1.21` for golang)
- `parallel: <parallel_tests>` — runs N parallel instances
- Script varies by `project_type`:
  - `rails`: `bundle install && bundle exec rspec --format progress`
  - `node`: `npm ci && npm test`
  - `python`: `pip install -r requirements.txt && pytest --tb=short`
  - `golang`: `go test ./... -count=1`
- Artifacts: `coverage/` directory with 1 day expiry
- Coverage regex per type:
  - `rails`: `'/\(\d+.\d+\%\) covered/'`
  - `node`: `'/Lines\s*:\s*(\d+\.\d+)%/'`
  - `python`: `'/TOTAL.*\s+(\d+)%/'`

**`security-scan`** job (stage: `security`):
- Image: `registry.gitlab.com/security-products/dependency-scanning:latest`
- Needs: `["build-image"]`
- `allow_failure: true`
- Script: `gemnasium-maven-plugin scan`
- Artifacts report type: `dependency_scanning`
- `only` conditions: `[main, /^release\/.*/]`

**`deploy-<env>`** job (one per `deploy_environments`, stage: `deploy`):
- Image: `bitnami/kubectl:latest`
- Needs: `["test", "security-scan"]`
- `environment.name`: `<env>`
- `environment.url`: `https://<env>.example.com`
- Script:
  1. `kubectl config use-context ${KUBE_CONTEXT_<ENV_UPPER>}`
  2. `kubectl set image deployment/app app=$IMAGE_TAG -n <env>`
  3. `kubectl rollout status deployment/app -n <env>`
- `only` conditions:
  - `staging`: `[develop, /^feature\/.*/]`
  - `production`: `[main]`
- `when: manual` for `production`

### Helper Methods (private)

- `test_image` — returns the correct Docker image string for the `project_type`
- `test_script` — returns the test command array for the `project_type`
- `coverage_regex` — returns the coverage extraction regex or `nil` for golang
- `deploy_job(env)` — builds the deployment job hash for a given environment

## Expected Functionality

- `PipelineTemplateGenerator.new(project_type: "rails").generate` returns a Hash with all 7 jobs: `build-image`, `test`, `security-scan`, `deploy-staging`, `deploy-production`
- `PipelineTemplateGenerator.new(project_type: "node", parallel_tests: 8).generate` produces a `test` job with `parallel: 8`
- `PipelineTemplateGenerator.new(project_type: "invalid")` raises `ArgumentError` with message `"Unsupported project type: invalid. Must be one of: rails, node, python, golang"`
- The deploy-production job has `when: manual` but deploy-staging does not
- All `only:` conditions are correct arrays

## Acceptance Criteria

- `generate` returns a Hash that serializes to a valid `.gitlab-ci.yml` structure
- All four project types produce correct test images and scripts
- `parallel_tests` is correctly applied to the `test` job's `parallel` key
- Deploy jobs have correct `only` branches and `when: manual` for production
- `security-scan` job has `allow_failure: true` and proper artifact report type
- Invalid `project_type` raises `ArgumentError` immediately in the constructor
- All RSpec tests pass covering all four project types, custom parallelism, and error cases
