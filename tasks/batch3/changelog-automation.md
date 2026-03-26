# Task: Implement Automated Changelog Generation from Conventional Commits

## Background

The github-changelog-generator project (https://github.com/github-changelog-generator/github-changelog-generator) is a Ruby tool for generating changelogs from GitHub data. The project needs a new module that parses Conventional Commit messages, categorizes changes, calculates semantic version bumps, and generates Keep a Changelog formatted output.

## Files to Create/Modify

- `lib/github_changelog_generator/conventional.rb` (create) — Conventional Commit message parser and categorizer
- `lib/github_changelog_generator/semver_calculator.rb` (create) — Semantic version bump calculator based on commit types
- `lib/github_changelog_generator/changelog_formatter.rb` (create) — Keep a Changelog formatted output generator
- `spec/unit/conventional_spec.rb` (create) — Tests for Conventional Commit parsing
- `spec/unit/semver_calculator_spec.rb` (create) — Tests for version bump calculation
- `spec/unit/changelog_formatter_spec.rb` (create) — Tests for changelog formatting

## Requirements

### Conventional Commit Parser

- Implement a `ConventionalCommit` class that parses commit messages following the Conventional Commits spec (https://www.conventionalcommits.org):
  - Format: `type(scope): description`
  - Optional body and footer sections separated by blank lines
  - Breaking changes indicated by `!` after type/scope or `BREAKING CHANGE:` footer
- Supported types: `feat`, `fix`, `docs`, `style`, `refactor`, `perf`, `test`, `build`, `ci`, `chore`, `revert`
- Parse into structured data: `type` (string), `scope` (string or nil), `description` (string), `body` (string or nil), `breaking` (boolean), `footers` (hash of footer key-value pairs)
- Handle edge cases: missing scope, multi-line body, multiple footers, `BREAKING-CHANGE` (hyphenated variant)
- Return `nil` for messages that don't conform to Conventional Commits format (non-matching messages)

### Change Categorization

- Group parsed commits into changelog categories:
  - `feat` → "Added"
  - `fix` → "Fixed"
  - `perf` → "Performance"
  - `refactor` → "Changed"
  - `docs` → "Documentation"
  - `revert` → "Reverted"
  - `build`, `ci`, `test`, `style`, `chore` → "Maintenance"
  - Breaking changes (any type with `breaking: true`) → also listed under "BREAKING CHANGES"
- Within each category, sort entries alphabetically by scope (nil scope sorts last)

### Semantic Version Calculator

- Implement a `SemverCalculator` that determines the version bump from a list of parsed commits:
  - Any breaking change → **major** bump
  - Any `feat` (without breaking) → **minor** bump
  - Only `fix`, `perf`, `refactor`, etc. → **patch** bump
  - No conventional commits → no bump (return `nil`)
- Accept a current version string (e.g., `"1.2.3"`) and return the next version (e.g., `"2.0.0"` for a breaking change)
- Support pre-release versions: `"1.2.3-beta.1"` with a breaking change → `"2.0.0"` (drops pre-release suffix)
- Validate version format: raise `InvalidVersionError` for non-semver strings

### Changelog Formatter

- Generate output following Keep a Changelog format (https://keepachangelog.com):
  ```
  ## [1.1.0] - 2024-01-15

  ### Added
  - **auth**: implement OAuth2 login flow (#123)
  - add user profile page (#125)

  ### Fixed
  - **api**: correct pagination offset calculation (#124)

  ### BREAKING CHANGES
  - **auth**: OAuth1 support has been removed
  ```
- Each entry format: `- **scope**: description (#PR)` or `- description (#PR)` (no scope)
- Include a comparison link at the bottom: `[1.1.0]: https://github.com/org/repo/compare/v1.0.0...v1.1.0`
- Support generating changelog for a single release or appending to an existing changelog file (prepend new release above existing content)

### Expected Functionality

- Parsing `"feat(auth): add login endpoint"` returns `{type: "feat", scope: "auth", description: "add login endpoint", breaking: false}`
- Parsing `"fix!: resolve crash on startup"` returns `{type: "fix", scope: nil, description: "resolve crash on startup", breaking: true}`
- Parsing `"Updated readme"` (non-conventional) returns `nil`
- Version calculation: current `"1.2.3"` with commits `[feat, fix, fix]` returns `"1.3.0"`
- Version calculation: current `"1.2.3"` with commits `[fix, feat!]` returns `"2.0.0"` (breaking)
- Version calculation: current `"0.5.0"` with commits `[fix]` returns `"0.5.1"`
- Changelog output groups entries correctly by category with scope formatting

## Acceptance Criteria

- Conventional Commit parser handles all supported types, optional scopes, bodies, footers, and breaking change indicators
- Non-conforming messages return `nil` without error
- Change categorization groups commits into correct Keep a Changelog categories
- Breaking changes appear in both their type category and the "BREAKING CHANGES" section
- Semantic version bump is correct: breaking → major, feat → minor, fix → patch
- Pre-release suffix is dropped on version bump
- Invalid version strings raise `InvalidVersionError`
- Changelog output follows Keep a Changelog format with scope-prefixed entries and comparison links
- Tests cover parsing edge cases, categorization, version calculation, and formatted output generation
