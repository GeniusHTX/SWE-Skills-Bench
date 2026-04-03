# Task: Build an Automated Changelog Generator for GitHub Changelog Generator

## Background

GitHub Changelog Generator (https://github.com/github-changelog-generator/github-changelog-generator) is a tool for generating changelogs from GitHub data. The project needs a Python-based changelog automation module that parses Conventional Commit messages, categorizes changes, generates changelogs in Keep a Changelog format, determines semantic version bumps, and produces GitHub release notes. The module must handle merge commits, squash merges, and conventional commit footers.

## Files to Create/Modify

- `lib/changelog/commit_parser.py` (create) — `ConventionalCommitParser` class parsing commit messages into structured objects with type, scope, description, body, breaking change flag, and footer references
- `lib/changelog/changelog_builder.py` (create) — `ChangelogBuilder` class generating Keep a Changelog formatted Markdown from parsed commits, grouped by change type (Added, Changed, Deprecated, Removed, Fixed, Security)
- `lib/changelog/version_bumper.py` (create) — `VersionBumper` class determining semantic version bumps (major/minor/patch) from commit types and breaking change indicators
- `lib/changelog/release_notes.py` (create) — `ReleaseNotesGenerator` class producing GitHub-style release notes with contributor mentions, PR references, and categorized change summaries
- `tests/test_changelog_automation.py` (create) — Tests for commit parsing, changelog generation, version bumping, and release notes formatting

## Requirements

### ConventionalCommitParser

- `parse(message: str) -> dict`:
  - Parse Conventional Commit format: `type(scope): description`
  - Return `{"type": str, "scope": str|None, "description": str, "body": str|None, "breaking": bool, "footers": dict, "raw": str}`
  - Valid types: `"feat"`, `"fix"`, `"docs"`, `"style"`, `"refactor"`, `"perf"`, `"test"`, `"build"`, `"ci"`, `"chore"`, `"revert"`
  - Breaking change detection: `!` after type/scope (e.g., `feat!: ...`) OR `BREAKING CHANGE:` footer
  - Footers parsed as key-value: `"Refs: #123"` → `{"refs": "#123"}`, `"Reviewed-by: Name"` → `{"reviewed-by": "Name"}`
- `parse_many(messages: list[str]) -> list[dict]` — Parse multiple commit messages, skip unparseable ones (store in `parser.skipped: list[str]`)
- `is_conventional(message: str) -> bool` — Return True if message matches conventional commit format
- Malformed messages (no type prefix): return None from `parse()`, add to `skipped` in `parse_many()`

### ChangelogBuilder

- Constructor: `ChangelogBuilder(version: str, date: str, compare_url: str = None)`
- `add_commits(commits: list[dict]) -> None` — Accept parsed commits and categorize:
  - `feat` → `Added`
  - `fix` → `Fixed`
  - `perf` → `Changed`
  - `refactor` → `Changed`
  - `docs` → `Changed` (only if scope is not `"readme"`)
  - `revert` → `Removed`
  - `deprecate` (or commits with `deprecation` in description) → `Deprecated`
  - Breaking changes: also listed in a separate `BREAKING CHANGES` section regardless of type
- `build() -> str` — Generate Markdown in Keep a Changelog format:
  ```
  ## [{version}] - {date}

  ### BREAKING CHANGES
  - **scope**: description

  ### Added
  - **scope**: description (#PR)

  ### Fixed
  - description

  [{version}]: {compare_url}
  ```
- `build_full(previous_entries: str = "") -> str` — Generate the complete CHANGELOG.md with header, unreleased section, current version, and previous entries appended
- Entries within each section sorted alphabetically by scope (scopeless entries last)

### VersionBumper

- Constructor: `VersionBumper(current_version: str)` — Parse semver string `major.minor.patch` (with optional `v` prefix)
- `determine_bump(commits: list[dict]) -> str` — Return `"major"`, `"minor"`, or `"patch"`:
  - Any breaking change → `"major"` (unless current major is 0, then `"minor"`)
  - Any `feat` → `"minor"`
  - Only `fix`, `perf`, `docs`, `refactor`, etc. → `"patch"`
  - Empty commits list → `"patch"`
- `bump() -> str` — Apply the determined bump and return new version string (without `v` prefix)
- `bump_to(bump_type: str) -> str` — Manually bump by specified type
- Pre-release support: `VersionBumper("1.2.3-alpha.1").bump()` increments pre-release number for same-level bumps, promotes to release for higher-level bumps
- Invalid version format: raise `ValueError("Invalid semver: {version}")`

### ReleaseNotesGenerator

- Constructor: `ReleaseNotesGenerator(repo_url: str, version: str, date: str)`
- `generate(commits: list[dict], contributors: list[str] = None, prs: list[dict] = None) -> str`:
  - Header: `# Release {version} ({date})`
  - Highlights section: first 3 `feat` commits as bullet points
  - Change sections: same categorization as ChangelogBuilder
  - PR references: if commit description contains `(#123)`, link to `{repo_url}/pull/123`
  - Contributors section: `## Contributors\nThanks to @user1, @user2 for their contributions!`
  - Footer: `**Full Changelog**: {repo_url}/compare/v{prev}...v{version}`
- `generate_pr_summary(prs: list[dict]) -> str`:
  - Each PR: `{"number": int, "title": str, "author": str, "labels": list[str]}`
  - Group by label (first label used for grouping): feature, bugfix, documentation, maintenance
  - Format as bullet list with PR number and author

### Edge Cases

- Commit message with multi-line body and multiple footers: all footers parsed correctly
- Merge commit with message `"Merge pull request #42 from branch"`: extract PR number but skip if not conventional format
- Version `0.x.y`: breaking changes bump minor (not major) per semver spec
- Empty changelog (no commits since last version): generate section with `No changes.` text
- Commit with scope containing special chars (e.g., `feat(api/v2): ...`): scope is `"api/v2"`

## Expected Functionality

- Parsing `"feat(auth): add OAuth2 login flow\n\nImplements Google and GitHub providers.\n\nRefs: #42\nReviewed-by: Alice"` returns type=feat, scope=auth, description with PR ref, and two footers
- `VersionBumper("1.2.3")` with one `feat` commit bumps to `"1.3.0"`
- `VersionBumper("1.2.3")` with a breaking `fix!` commit bumps to `"2.0.0"`
- `ChangelogBuilder("1.3.0", "2024-01-15")` with mixed commits produces grouped Markdown sections
- `ReleaseNotesGenerator` produces GitHub-formatted release notes with PR links and contributor mentions

## Acceptance Criteria

- `ConventionalCommitParser` correctly parses type, scope, description, body, breaking flag, and footers from conventional commit messages
- Non-conventional messages are skipped without errors
- `ChangelogBuilder` produces Keep a Changelog formatted Markdown with correct section grouping and alphabetical ordering
- `VersionBumper` determines correct semver bumps including pre-release and 0.x.y handling
- `ReleaseNotesGenerator` produces release notes with PR links, contributor mentions, and comparison URL
- All tests pass with `pytest`
