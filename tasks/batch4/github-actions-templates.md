# Task: Create GitHub Actions CI/CD Workflows for a Python Library

## Background

The starter-workflows repository (https://github.com/actions/starter-workflows) provides official GitHub Actions workflow templates. A comprehensive set of CI/CD workflows is needed for a Python library project that covers automated testing across multiple Python versions, package building and publishing to PyPI, security scanning, and release automation — all following GitHub Actions best practices for caching, secrets handling, and job composition.

## Files to Create/Modify

- `ci/python-library-ci.yml` (create) — CI workflow running tests, linting, and type checking on push and PR
- `deployments/python-library-publish.yml` (create) — Publish workflow triggered on GitHub Release to build and upload to PyPI
- `code-scanning/python-security-scan.yml` (create) — Security scanning workflow running on schedule and PR
- `automation/python-release-drafter.yml` (create) — Release drafter that auto-generates changelogs from PR labels

## Requirements

### CI Workflow (`python-library-ci.yml`)

- Trigger on `push` to `main` and `develop` branches, and on `pull_request` to `main`
- Use a matrix strategy to test against Python 3.9, 3.10, 3.11, and 3.12 on `ubuntu-latest`
- Steps must include: checkout, Python setup with pip caching, dependency install via `pip install -e ".[dev]"`, lint with `ruff check .`, type check with `mypy src/`, and test with `pytest --cov=src --cov-report=xml`
- Upload the coverage report as an artifact using `actions/upload-artifact@v4`
- A separate job named `all-checks-pass` must run after the matrix job and act as a required status check (succeeds only if all matrix jobs succeed)
- All action references must use pinned major versions (e.g., `@v4`, `@v5`)

### Publish Workflow (`python-library-publish.yml`)

- Trigger on `release` event with type `published`
- Use `id-token: write` permission for trusted PyPI publishing (no API token needed)
- Build the package using `python -m build` producing both sdist and wheel
- Upload to PyPI using `pypa/gh-action-pypi-publish@release/v1`
- A preceding job must run the full test suite before publishing proceeds; publishing must not run if tests fail
- The workflow must also upload the built distributions as release assets on the GitHub Release

### Security Scan Workflow (`python-security-scan.yml`)

- Trigger on `pull_request` to `main` and on a weekly cron schedule (`0 6 * * 1`)
- Run `pip-audit` to check dependencies for known vulnerabilities
- Run `bandit -r src/` to check for common security issues in source code
- Both checks must run as separate steps; the workflow must fail if either reports findings
- Results from `pip-audit` must be uploaded as a SARIF file using `github/codeql-action/upload-sarif@v3`

### Release Drafter Workflow (`python-release-drafter.yml`)

- Trigger on `push` to `main` and on `pull_request` events (types: opened, reopened, synchronize)
- Use `release-drafter/release-drafter@v5` action
- Categories must include: "Features" (labels: `feature`, `enhancement`), "Bug Fixes" (labels: `bug`, `fix`), "Documentation" (labels: `docs`, `documentation`), and "Breaking Changes" (labels: `breaking`)
- Include a `.github/release-drafter.yml` configuration file that defines the category labels and version resolver

### Expected Functionality

- A push to `main` triggers the CI workflow, running 4 parallel matrix jobs (one per Python version) each executing lint, type-check, and test steps
- A PR to `main` triggers CI, security scan, and release drafter workflows
- Publishing a GitHub Release triggers the publish workflow, which tests, builds, and publishes to PyPI only if tests pass
- The weekly cron schedule triggers the security scan independently of PRs
- The `all-checks-pass` job in CI fails if any matrix combination fails

## Acceptance Criteria

- All four workflow files are valid YAML and parse without errors
- The CI workflow uses a matrix strategy across 4 Python versions with pip caching enabled
- The CI workflow includes an `all-checks-pass` gate job that depends on all matrix jobs
- The publish workflow enforces test passage before publishing and uses trusted publishing with `id-token: write`
- The security scan workflow runs both `pip-audit` and `bandit` and uploads SARIF results
- The release drafter categorizes PRs by label and generates draft release notes automatically
- All action references use pinned major versions, not `@latest` or `@main`
- Secrets are accessed only via `${{ secrets.* }}` expressions and never hardcoded
