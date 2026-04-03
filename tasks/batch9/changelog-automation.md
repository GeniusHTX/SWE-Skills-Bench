# Task: Build a Changelog Generator from Conventional Commits

## Background

The github-changelog-generator project (https://github.com/github-changelog-generator/github-changelog-generator) automates changelog creation. A new Ruby module is needed that parses Conventional Commits from git history, categorizes them into Keep a Changelog sections, calculates the next semantic version, generates formatted CHANGELOG.md content, and provides a CLI for integration into release workflows.

## Files to Create/Modify

- `lib/changelog/commit_parser.rb` (create) — `Changelog::CommitParser` class that parses Conventional Commit messages into structured objects with type, scope, description, body, breaking change flag, and footer metadata
- `lib/changelog/categorizer.rb` (create) — `Changelog::Categorizer` class that maps commit types to Keep a Changelog sections (Added, Changed, Deprecated, Removed, Fixed, Security) and filters non-user-facing types
- `lib/changelog/version_calculator.rb` (create) — `Changelog::VersionCalculator` class that determines the next semantic version based on commit types (MAJOR for breaking, MINOR for feat, PATCH for fix)
- `lib/changelog/renderer.rb` (create) — `Changelog::Renderer` class that formats categorized commits into Markdown following the Keep a Changelog 1.1.0 specification
- `lib/changelog/cli.rb` (create) — CLI entry point using `optparse`: `changelog generate [--from TAG] [--to TAG] [--output FILE] [--repo-url URL]`
- `spec/changelog/commit_parser_spec.rb` (create) — RSpec tests for commit parsing with edge cases
- `spec/changelog/categorizer_spec.rb` (create) — RSpec tests for categorization logic
- `spec/changelog/version_calculator_spec.rb` (create) — RSpec tests for version calculation
- `spec/changelog/renderer_spec.rb` (create) — RSpec tests for Markdown rendering

## Requirements

### Commit Parser (`commit_parser.rb`)

- Class `Changelog::CommitParser` with method `parse(message: String) -> ParsedCommit`
- `ParsedCommit` attributes: `type` (String), `scope` (String or nil), `description` (String), `body` (String or nil), `breaking` (Boolean), `footers` (Hash)
- Regex pattern: `/^(?<type>\w+)(?:\((?<scope>[^)]+)\))?(?<breaking>!)?:\s*(?<description>.+)$/`
- Parse body: everything after first blank line until footer section
- Parse footers: lines matching `^(?<key>[\w-]+):\s*(?<value>.+)$` or `^(?<key>[\w-]+)\s#(?<value>.+)$`
- Detect breaking change: `!` suffix on type, or `BREAKING CHANGE:` in footer, or `BREAKING-CHANGE:` in footer
- Handle multi-line bodies and footers with continuation lines (indented)
- Return `nil` for messages that don't match Conventional Commits format
- Strip leading/trailing whitespace from all parsed fields

### Categorizer (`categorizer.rb`)

- Class `Changelog::Categorizer` with method `categorize(commits: Array<ParsedCommit>) -> Hash<String, Array<ParsedCommit>>`
- Default type-to-section mapping:
  - `feat` → "Added"
  - `fix` → "Fixed"
  - `perf` → "Changed"
  - `refactor` → "Changed"
  - `revert` → "Removed"
  - `deps` / `build` → "Changed" (only if scope includes "deps")
  - `security` → "Security"
  - `deprecate` → "Deprecated"
- Types `docs`, `style`, `test`, `ci`, `chore` are excluded by default
- Method accepts `include_all: false` parameter; when `true`, include excluded types under "Other"
- Breaking changes (regardless of type) also appear in a special "BREAKING CHANGES" section with their full body/footer
- Method `add_mapping(type: String, section: String)` — Allows custom type-to-section mappings

### Version Calculator (`version_calculator.rb`)

- Class `Changelog::VersionCalculator` with method `next_version(current: String, commits: Array<ParsedCommit>) -> String`
- `current` follows semver format `"MAJOR.MINOR.PATCH"` or `"vMAJOR.MINOR.PATCH"`
- Rules:
  - Any commit with `breaking: true` → bump MAJOR, reset MINOR and PATCH to 0
  - Any `feat` type (without breaking) → bump MINOR, reset PATCH to 0
  - Only `fix`/`perf` types → bump PATCH
  - No categorizable commits → return current version unchanged
- If `current` starts with `v`, output also starts with `v`
- Method `next_version_pre(current, commits, pre_tag: "rc") -> String` — For pre-release: appends `-rc.N` where N increments

### Renderer (`renderer.rb`)

- Class `Changelog::Renderer` with method `render(version:, date:, categories:, repo_url: nil, previous_version: nil) -> String`
- Output format follows Keep a Changelog 1.1.0:
  ```markdown
  ## [1.2.0] - 2024-01-15

  ### Added
  - **scope**: description ([#123](repo_url/issues/123))

  ### Fixed
  - description

  [1.2.0]: repo_url/compare/v1.1.0...v1.2.0
  ```
- Each entry format: `- **scope**: description` (with scope) or `- description` (without scope)
- If commit description references `#NNN`, convert to link using `repo_url`
- If `repo_url` and `previous_version` are provided, append comparison link at bottom
- Method `render_full(entries: Array, unreleased_categories: Hash) -> String` — Renders full CHANGELOG.md with header, unreleased section, and all version entries
- Section order: BREAKING CHANGES, Added, Changed, Deprecated, Removed, Fixed, Security

### Expected Functionality

- Parsing `"feat(auth): add OAuth2 support\n\nBREAKING CHANGE: removed basic auth"` returns type=feat, scope=auth, breaking=true
- Categorizing [feat, fix, fix, docs] returns {"Added" => [1 commit], "Fixed" => [2 commits]} (docs excluded)
- `next_version("1.2.3", [fix, fix])` returns `"1.2.4"`; `next_version("1.2.3", [feat])` returns `"1.3.0"`; `next_version("1.2.3", [breaking feat])` returns `"2.0.0"`
- Rendering version 1.2.0 with 2 Added and 1 Fixed produces valid Markdown with 2 sections

## Acceptance Criteria

- Commit parser handles all Conventional Commits edge cases: scoped, unscoped, breaking with `!`, breaking via footer, multi-line body
- Categorizer correctly maps types to Keep a Changelog sections and excludes non-user-facing types
- Version calculator follows semver rules: breaking → MAJOR, feat → MINOR, fix → PATCH
- Renderer output is valid Markdown matching Keep a Changelog 1.1.0 format with comparison links
- Non-conventional commit messages return nil from parser (no crash)
- `python -m pytest /workspace/tests/test_changelog_automation.py -v --tb=short` passes
