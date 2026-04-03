# Task: Set Up Automated Changelog Generation and Release Workflow

## Background

An open-source Node.js library needs automated changelog generation from Conventional Commits, semantic version bumping, and GitHub Release creation. The setup includes commitlint for enforcing commit format, a changelog generator that produces Keep a Changelog formatted output, and a GitHub Actions release workflow that automates the full release process.

## Files to Create/Modify

- `commitlint.config.js` (create) — Commitlint configuration enforcing Conventional Commits format
- `.husky/commit-msg` (create) — Git hook running commitlint on each commit message
- `scripts/generate-changelog.js` (create) — Node.js script that parses git log, categorizes commits, and generates changelog entries
- `scripts/bump-version.js` (create) — Node.js script that determines next semver version from commit types
- `.github/workflows/release.yml` (create) — GitHub Actions workflow for automated releases
- `CHANGELOG.md` (create) — Initial changelog file following Keep a Changelog format

## Requirements

### Commitlint Configuration (`commitlint.config.js`)

- Extends `@commitlint/config-conventional`.
- Custom rules:
  - `type-enum`: allow `feat`, `fix`, `docs`, `style`, `refactor`, `perf`, `test`, `chore`, `ci`, `build`, `revert`.
  - `subject-case`: disallow `start-case`, `pascal-case`, `upper-case`.
  - `subject-max-length`: max 72 characters.
  - `body-max-line-length`: max 100 characters.
  - `footer-max-line-length`: max 100 characters.
- Export as ES module (`export default`).

### Git Hook (`.husky/commit-msg`)

- Runs `npx --no -- commitlint --edit $1`.
- Executable permissions (`chmod +x`).

### Changelog Generator (`scripts/generate-changelog.js`)

- `parseCommits(fromTag: string | null, toRef: string = "HEAD") -> Commit[]`:
  - Run `git log --format="%H|%s|%b|%an|%ae|%aI" <fromTag>...<toRef>`.
  - Parse each line into: `{ hash, type, scope, description, body, breaking, author, date, prNumber }`.
  - Extract PR number from commit body footer matching `(#\d+)` pattern.
  - Detect breaking changes from `!` after type or `BREAKING CHANGE:` in footer.

- `categorizeCommits(commits: Commit[]) -> CategorizedCommits`:
  - Map commit types to Keep a Changelog sections:
    - `feat` → `Added`
    - `fix` → `Fixed`
    - `perf` → `Changed`
    - `refactor` → `Changed`
    - `revert` → `Removed`
    - `docs`, `style`, `test`, `chore`, `ci`, `build` → excluded from changelog
  - Breaking changes → `Breaking Changes` section (regardless of type).

- `generateMarkdown(version: string, date: string, categorized: CategorizedCommits, repoUrl: string) -> string`:
  - Output format following Keep a Changelog:
    ```
    ## [1.3.0] - 2026-01-15

    ### Breaking Changes

    - **auth**: Remove legacy OAuth1 support (#42)

    ### Added

    - **api**: Add batch processing endpoint (#38)
    - **cli**: Add --verbose flag for debug output (#35)

    ### Fixed

    - **parser**: Handle nested brackets correctly (#40)
    - Fix memory leak in stream processing (#39)

    ### Changed

    - **core**: Improve parsing performance by 30% (#37)
    ```
  - Each entry format: `- **{scope}**: {description} (#{prNumber})` or `- {description} (#{prNumber})` if no scope.
  - Entries sorted by scope (scoped first, then unscoped), then alphabetically.

- `updateChangelog(changelogPath: string, newEntry: string, version: string, previousVersion: string, repoUrl: string)`:
  - Read existing CHANGELOG.md.
  - Insert new version entry after the `## [Unreleased]` section.
  - Update comparison links at bottom: add `[{version}]: {repoUrl}/compare/v{previousVersion}...v{version}` and update `[Unreleased]` link to `{repoUrl}/compare/v{version}...HEAD`.

### Version Bumper (`scripts/bump-version.js`)

- `determineNextVersion(currentVersion: string, commits: Commit[]) -> { version: string, reason: string }`:
  - Breaking changes → major bump (e.g., `1.2.3` → `2.0.0`).
  - Any `feat` commits → minor bump (e.g., `1.2.3` → `1.3.0`).
  - Only `fix` commits → patch bump (e.g., `1.2.3` → `1.2.4`).
  - No releasable commits → return `null`.
- Read current version from `package.json`.
- Write new version to `package.json` (update `version` field).
- Create git tag `v{version}`.

### Release Workflow (`.github/workflows/release.yml`)

- Trigger: `workflow_dispatch` with optional input `release_type` (choice: `auto`, `major`, `minor`, `patch`; default: `auto`).
- Steps:
  1. Checkout with full git history (`fetch-depth: 0`).
  2. Setup Node.js 20 with npm cache.
  3. Install dependencies (`npm ci`).
  4. Run `node scripts/bump-version.js` (or use input override if not `auto`).
  5. Run `node scripts/generate-changelog.js`.
  6. Commit changes to `CHANGELOG.md` and `package.json` with message `chore(release): v{version}`.
  7. Create and push git tag `v{version}`.
  8. Push commit to default branch.
  9. Create GitHub Release using `softprops/action-gh-release@v1` with the changelog entry as release body.
  10. Publish to npm (`npm publish`).
- Permissions: `contents: write`, `packages: write`.
- Uses `GITHUB_TOKEN` for git push and release creation, `NPM_TOKEN` secret for npm publish.

### Initial Changelog (`CHANGELOG.md`)

```markdown
# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

[Unreleased]: https://github.com/OWNER/REPO/compare/v1.0.0...HEAD
```

### Expected Functionality

- Commit `feat(api): add batch endpoint (#38)` + commit `fix(parser): handle brackets (#40)` → generate-changelog produces `## [1.1.0]` with `Added` and `Fixed` sections.
- Commit `feat!: remove legacy auth` → bump-version produces major version bump, changelog has `Breaking Changes` section.
- `workflow_dispatch` with `auto` → runs full pipeline: determine version, generate changelog, commit, tag, release, publish.
- Commit message `docs: update README` → excluded from changelog (type `docs` not mapped to any section).
- `commitlint` rejects commit message `updated stuff` (missing type prefix).

## Acceptance Criteria

- Commitlint enforces Conventional Commits format with custom type allowlist and length limits.
- Changelog generator parses git log into typed commits with scope, PR number, and breaking change detection.
- Generated changelog follows Keep a Changelog format with sections: Breaking Changes, Added, Fixed, Changed, Removed.
- Entries are formatted as `- **{scope}**: {description} (#{pr})` and sorted by scope then alphabetically.
- Version bumper determines semver increment from commit types: breaking→major, feat→minor, fix→patch.
- CHANGELOG.md is updated in-place with new entry inserted after `[Unreleased]` and comparison links updated.
- Release workflow automates: version bump, changelog generation, git commit/tag/push, GitHub Release creation, and npm publish.
- Non-releasable commits (docs, test, chore, ci, style, build) are excluded from changelog output.
