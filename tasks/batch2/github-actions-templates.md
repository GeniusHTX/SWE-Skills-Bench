# Task: Create a Python CI Workflow Template for GitHub Actions

## Background

The starter-workflows repository (https://github.com/actions/starter-workflows) provides official GitHub Actions workflow templates. A new CI workflow template is needed specifically for Python projects using pytest, covering linting, testing across multiple Python versions, and coverage reporting.

## Files to Create

- `ci/python-pytest.yml` — GitHub Actions workflow file for Python CI

## Requirements

### Workflow Triggers

- Trigger on push to `main` and on pull requests targeting `main`

### Job Structure

- A test job that runs on `ubuntu-latest`
- Matrix strategy testing across at least two Python versions
- Steps for: checkout, Python setup, dependency installation, lint check, and test execution with pytest

### CI Best Practices

- Pin action versions to specific tags (e.g., `@v4`, not `@latest`)
- Cache pip dependencies to speed up subsequent runs
- Upload test coverage results as an artifact or to a coverage service
- Set appropriate permissions on the workflow

### Validation

- The workflow YAML must be syntactically valid and structurally correct per the GitHub Actions schema

## Expected Functionality

- The workflow runs pytest across multiple Python versions on every push and PR
- Dependencies are cached to reduce installation time on subsequent runs
- Coverage data is collected and made available as a workflow artifact

## Acceptance Criteria

- The workflow triggers on pushes to `main` and pull requests targeting `main`.
- The CI job runs across multiple Python versions and includes checkout, environment setup, dependency installation, linting, testing, and coverage handling.
- Action versions are pinned to explicit versions rather than floating tags.
- Dependency caching is configured so repeated workflow runs avoid unnecessary package reinstalls.
- Workflow permissions and artifact handling follow normal GitHub Actions best practices for a Python CI template.
