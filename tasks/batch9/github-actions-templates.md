# Task: Create Reusable CI/CD Workflow Templates for a Full-Stack Application

## Background

The starter-workflows repository (https://github.com/actions/starter-workflows) provides GitHub Actions templates organized by category. New workflow templates are needed for a full-stack application stack that includes a Python FastAPI backend, a React frontend, and deployment to AWS ECS using Docker. Each template must follow the repository's conventions: a `.yml` workflow file and a corresponding `.properties.json` metadata file.

## Files to Create/Modify

- `ci/python-fastapi.yml` (create) — CI workflow template for a FastAPI application with linting, type checking, and testing across Python 3.10, 3.11, and 3.12
- `ci/properties/python-fastapi.properties.json` (create) — Metadata for the FastAPI CI template
- `ci/react-vite.yml` (create) — CI workflow template for a React + Vite application with linting, unit tests, and build verification across Node 18.x and 20.x
- `ci/properties/react-vite.properties.json` (create) — Metadata for the React Vite CI template
- `deployments/aws-ecs-fullstack.yml` (create) — Deployment workflow template that builds Docker images for frontend and backend, pushes to Amazon ECR, and deploys to ECS with rolling update
- `deployments/properties/aws-ecs-fullstack.properties.json` (create) — Metadata for the ECS deployment template
- `automation/dependency-review.yml` (create) — Automation workflow that runs on pull requests to check for dependency vulnerabilities and license compliance
- `automation/properties/dependency-review.properties.json` (create) — Metadata for the dependency review template

## Requirements

### FastAPI CI Template (`ci/python-fastapi.yml`)

- Trigger on `push` to `$default-branch` and `pull_request` to `$default-branch` (using the repository template variable)
- Use `strategy.matrix` for Python versions `["3.10", "3.11", "3.12"]`
- Steps: checkout, setup Python with pip caching, install dependencies via `pip install -r requirements.txt`, run linter with `ruff check .`, run type checker with `mypy .`, run tests with `pytest --cov --cov-report=xml`
- Upload coverage using `codecov/codecov-action@v3`
- Job name: `test`

### React Vite CI Template (`ci/react-vite.yml`)

- Trigger on `push` to `$default-branch` and `pull_request` to `$default-branch`
- Use `strategy.matrix` for Node versions `[18.x, 20.x]`
- Steps: checkout, setup Node.js with npm caching, `npm ci`, `npm run lint`, `npm test -- --coverage`, `npm run build`
- Upload build artifacts using `actions/upload-artifact@v4` with path `dist/`
- Job name: `build`

### ECS Deployment Template (`deployments/aws-ecs-fullstack.yml`)

- Trigger on `push` to `$default-branch` only
- Define environment variables: `AWS_REGION`, `ECR_REPOSITORY_BACKEND`, `ECR_REPOSITORY_FRONTEND`, `ECS_CLUSTER`, `ECS_SERVICE_BACKEND`, `ECS_SERVICE_FRONTEND`, `ECS_TASK_DEFINITION`
- Job `deploy` runs on `ubuntu-latest` with permissions `id-token: write` and `contents: read`
- Steps: checkout, configure AWS credentials via `aws-actions/configure-aws-credentials@v4` using OIDC (`role-to-assume`), login to ECR via `aws-actions/amazon-ecr-login@v2`, build and push backend image tagged with `${{ github.sha }}`, build and push frontend image tagged with `${{ github.sha }}`, render new ECS task definition for backend via `aws-actions/amazon-ecs-render-task-definition@v1`, render new ECS task definition for frontend, deploy backend via `aws-actions/amazon-ecs-deploy-task-definition@v2` with `wait-for-service-stability: true`, deploy frontend similarly

### Dependency Review Template (`automation/dependency-review.yml`)

- Trigger on `pull_request` only
- Single job `dependency-review` on `ubuntu-latest`
- Steps: checkout, run `actions/dependency-review-action@v4` with `fail-on-severity: high`, `deny-licenses: GPL-3.0`, and `comment-summary-in-pr: always`

### Properties Files

- Each `.properties.json` must contain: `name` (string), `description` (string), `iconName` (string matching an icon in the `icons/` directory or using `octicon <name>`), `categories` (array of strings or null)
- `python-fastapi.properties.json`: name `"Python FastAPI"`, iconName `"python"`, categories `["Continuous integration", "Python", "FastAPI"]`
- `react-vite.properties.json`: name `"React with Vite"`, iconName `"nodejs"`, categories `["Continuous integration", "JavaScript", "React", "Vite"]`
- `aws-ecs-fullstack.properties.json`: name `"Deploy Full-Stack to Amazon ECS"`, iconName `"aws"`, categories `["Deployment", "AWS", "Docker", "ECS"]`, include `"creator"` field set to `"actions"`
- `dependency-review.properties.json`: name `"Dependency Review"`, iconName `"octicon shield-check"`, categories `["Automation", "Security"]`

### Expected Functionality

- Each workflow YAML file is valid GitHub Actions syntax parseable by `actionlint`
- The FastAPI workflow installs dependencies, runs ruff and mypy, executes pytest with coverage, and uploads coverage reports
- The React Vite workflow builds and tests across two Node versions and publishes build artifacts
- The ECS deployment workflow builds two Docker images, pushes them to ECR, and performs a rolling ECS deployment with stability wait
- The dependency review workflow blocks PRs that introduce high-severity vulnerabilities or GPL-3.0 licensed dependencies

## Acceptance Criteria

- All 4 workflow YAML files are syntactically valid and parseable as GitHub Actions workflows
- All 4 properties JSON files contain the required `name`, `description`, `iconName`, and `categories` fields
- Workflow trigger events use `$default-branch` template variable (not hardcoded branch names)
- Matrix strategies specify the correct language versions
- The ECS deployment uses OIDC authentication (`role-to-assume`) rather than static access keys
- Dependency review action is configured with `fail-on-severity` and `deny-licenses` parameters
- `python -m pytest /workspace/tests/test_github_actions_templates.py -v --tb=short` passes
