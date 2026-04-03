# Task: Create a Reusable CI/CD Workflow for Node.js Libraries in the Starter Workflows Repository

## Background

The GitHub Actions starter-workflows repository (https://github.com/actions/starter-workflows) provides official workflow templates for common CI/CD patterns. The task is to create a new reusable workflow template for Node.js library projects that covers testing across multiple Node.js versions, artifact caching, code coverage reporting, npm publishing on release tags, and security auditing — all as a single, parameterized template that library authors can adopt with minimal configuration.

## Files to Create/Modify

- `ci/node-library-ci.yml` (create) — The main CI workflow template for Node.js library testing, coverage, and security audit
- `deployments/node-library-publish.yml` (create) — The publish workflow template triggered on version tags to publish to npm
- `ci/node-library-ci.properties.json` (create) — Template metadata describing the CI workflow's purpose, categories, and icon
- `deployments/node-library-publish.properties.json` (create) — Template metadata for the publish workflow

## Requirements

### CI Workflow (`ci/node-library-ci.yml`)

- Triggers: `push` to `main` and `master` branches, and `pull_request` to these branches
- Must define a matrix strategy testing on Node.js versions 18, 20, and 22
- Must run on `ubuntu-latest` runner
- Steps must include: checkout, Node.js setup with version matrix, dependency caching using `actions/cache` keyed on `package-lock.json` hash, `npm ci`, `npm test`, `npm run lint` (if the script exists), and `npm audit --audit-level=high`
- If a `coverage` npm script exists, a coverage step must run and upload the coverage artifact using `actions/upload-artifact`
- The workflow must set `fail-fast: false` on the matrix so all versions are tested even if one fails
- A concurrency group must be configured to cancel in-progress runs for the same branch/PR

### Publish Workflow (`deployments/node-library-publish.yml`)

- Triggers: `push` of tags matching `v*.*.*` (semver format)
- Runs on `ubuntu-latest` with Node.js 20
- Steps: checkout, Node.js setup with `registry-url: https://registry.npmjs.org`, `npm ci`, `npm test` (must pass before publishing), `npm publish` with `NODE_AUTH_TOKEN` from secrets
- Must include a condition or step that verifies the tag version matches the version in `package.json` before publishing
- Must create a GitHub Release with auto-generated release notes using `actions/create-release` or `gh release create`

### Properties Files

- Each `.properties.json` must include: `name`, `description`, `iconName`, `categories` (array), and `filePatterns` (array of glob patterns the workflow applies to, e.g., `["package.json"]`)
- `categories` for the CI workflow: `["Node.js", "CI"]`
- `categories` for the publish workflow: `["Node.js", "Deployment", "npm"]`

### Template Placeholders

- Use `$default-branch` placeholder for the default branch name (resolved by GitHub at template adoption time)
- Use `${{ secrets.NPM_TOKEN }}` for the npm authentication token
- Include YAML comments explaining each major section so adopters understand the workflow

### Security Considerations

- The npm audit step must fail the workflow if high or critical vulnerabilities are found
- The `NODE_AUTH_TOKEN` must only be referenced in the publish workflow, never in the CI workflow
- The `permissions` key must be set to minimum required: `contents: read` for CI, `contents: write` and `id-token: write` for publish
- Artifact uploads must not include `node_modules/`

## Expected Functionality

- A library author selects the CI template from GitHub's "New Workflow" UI and gets a working test matrix for Node.js 18/20/22 that caches dependencies, runs tests, and audits packages
- Pushing to `main` triggers the CI workflow, which runs tests on all three Node.js versions in parallel
- Tagging a commit `v1.2.3` triggers the publish workflow, which runs tests, verifies version consistency, publishes to npm, and creates a GitHub Release
- A PR with a failing test on Node.js 18 but passing on 20 and 22 still shows all three results (fail-fast disabled)

## Acceptance Criteria

- The CI workflow defines a 3-version Node.js matrix with dependency caching, test execution, lint execution, coverage upload, and `npm audit`
- The CI workflow uses concurrency groups to cancel redundant runs
- The publish workflow verifies tag-to-package.json version consistency before running `npm publish`
- The publish workflow creates a GitHub Release with release notes
- Both `.properties.json` files contain valid `name`, `description`, `iconName`, `categories`, and `filePatterns` fields
- Workflow permissions are restricted to the minimum required for each workflow
- Template placeholders (`$default-branch`, `${{ secrets.NPM_TOKEN }}`) are used correctly
