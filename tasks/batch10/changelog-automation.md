# Task: Implement Conventional Commit Parser and Changelog Generator for github-changelog-generator

## Background

The `github-changelog-generator` Ruby gem (`github-changelog-generator/github-changelog-generator`) currently generates changelogs from GitHub pull requests and issues, but lacks built-in support for parsing Conventional Commit messages and mapping them to Keep a Changelog sections. A new module is needed within `lib/github_changelog_generator/` that parses commit messages following the Conventional Commits specification, categorizes them into changelog sections (Added, Changed, Fixed, Deprecated, Removed, Security), computes semantic version bumps, and renders the output in Keep a Changelog format with comparison links.

## Files to Create/Modify

- `lib/github_changelog_generator/conventional_commit.rb` — Parser for Conventional Commit messages (new)
- `lib/github_changelog_generator/changelog_renderer.rb` — Renderer that produces Keep a Changelog formatted output (new)
- `lib/github_changelog_generator/version_calculator.rb` — Semantic version calculator based on parsed commit types (new)
- `spec/unit/conventional_commit_spec.rb` — RSpec tests for the commit parser (new)
- `spec/unit/changelog_renderer_spec.rb` — RSpec tests for the renderer (new)
- `spec/unit/version_calculator_spec.rb` — RSpec tests for the version calculator (new)

## Requirements

### Conventional Commit Parser

- Implement `ConventionalCommit.parse(message)` that returns a struct/object with: `type`, `scope` (optional), `description`, `body` (optional), `footers` (hash), `breaking` (boolean)
- Supported types: `feat`, `fix`, `docs`, `style`, `refactor`, `perf`, `test`, `chore`, `ci`, `build`, `revert`
- Breaking changes detected via `!` after type/scope (e.g., `feat!: drop support`) OR via `BREAKING CHANGE:` footer
- Scope extracted from parentheses: `feat(auth): add login` → scope is `auth`
- Multi-line body separated from description by a blank line
- Footers parsed from `key: value` or `key #value` patterns in the trailer section (e.g., `Reviewed-by: Alice`, `Fixes #42`)
- Return `nil` for messages that don't match the conventional commit pattern
- Handle edge cases: type with no description (invalid, return nil), empty message (return nil), scope with special characters like `-` and `_`

### Changelog Renderer

- Implement `ChangelogRenderer.new(commits:, version:, date:, repo_url:)` that accepts an array of parsed commits
- `render()` produces a Markdown string in Keep a Changelog format with sections: `Added` (feat), `Changed` (refactor, perf), `Fixed` (fix), `Deprecated` (commits with `Deprecated:` footer), `Removed` (revert), `Security` (commits with `Security:` footer or type `chore` with scope `security`)
- Empty sections are omitted from the output
- Each entry formatted as `- DESCRIPTION (#PR)` when a `PR` footer exists, otherwise just `- DESCRIPTION`
- Scoped entries formatted as `- **scope:** description`
- Breaking changes collected into a `BREAKING CHANGES` subsection under their respective type section
- Output must include a comparison link at the bottom: `[VERSION]: REPO_URL/compare/PREV_TAG...vVERSION`
- Entries within each section sorted alphabetically by description

### Version Calculator

- Implement `VersionCalculator.new(current_version:)` with `next_version(commits:)`
- If any commit has `breaking: true` → bump major (unless major is 0, in which case bump minor)
- If any commit is `feat` type → bump minor
- If commits contain only `fix`, `perf`, `refactor`, `docs`, `style`, `test`, `chore`, `ci`, `build` → bump patch
- If no commits provided → return current version unchanged
- Parse and produce versions in `MAJOR.MINOR.PATCH` format
- Handle pre-release versions: `1.0.0-beta.1` → breaking change → `1.0.0-beta.2` (increment pre-release), `1.0.0-beta.1` with `--graduate` flag → `1.0.0`
- Reject invalid version strings (missing components, negative numbers, non-numeric parts)

### Expected Functionality

- `ConventionalCommit.parse("feat(auth): add OAuth2 login")` → type `feat`, scope `auth`, description `add OAuth2 login`, breaking `false`
- `ConventionalCommit.parse("fix!: resolve crash on empty input\n\nBREAKING CHANGE: input validation now required")` → breaking `true`, footer `BREAKING CHANGE` present
- `ConventionalCommit.parse("not a conventional commit")` → returns `nil`
- `ConventionalCommit.parse("")` → returns `nil`
- `ConventionalCommit.parse("feat:")` → returns `nil` (no description)
- Renderer with 2 feat commits and 1 fix commit → output contains `### Added` with 2 entries and `### Fixed` with 1 entry; no `### Changed` section
- Renderer with scoped commit `feat(ui): add dark mode` → entry reads `- **ui:** add dark mode`
- `VersionCalculator.new(current_version: "1.2.3").next_version(commits:)` with one `feat` commit → `"1.3.0"`
- `VersionCalculator.new(current_version: "1.2.3").next_version(commits:)` with one breaking `fix!` → `"2.0.0"`
- `VersionCalculator.new(current_version: "0.5.0").next_version(commits:)` with breaking change → `"0.6.0"` (major 0 special case)
- `VersionCalculator.new(current_version: "1.2.3").next_version(commits: [])` → `"1.2.3"`

## Acceptance Criteria

- `bundle exec rspec spec/unit/conventional_commit_spec.rb` passes all tests
- `bundle exec rspec spec/unit/changelog_renderer_spec.rb` passes all tests
- `bundle exec rspec spec/unit/version_calculator_spec.rb` passes all tests
- Commit parser correctly extracts type, scope, description, body, footers, and breaking flag from well-formed messages
- Commit parser returns nil for non-conforming messages including empty strings and missing descriptions
- Renderer produces valid Markdown with correct section headers and omits empty sections
- Renderer sorts entries alphabetically within sections
- Breaking changes appear in a dedicated subsection
- Comparison links use the correct tag format relative to the repo URL
- Version calculator applies semver rules including the major-0 special case
- Pre-release version bumping increments the pre-release segment correctly
- Invalid version strings are rejected with a descriptive error
