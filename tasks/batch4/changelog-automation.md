# Task: Build an Automated Changelog Generator from Conventional Commits

## Background

The github-changelog-generator repository (https://github.com/github-changelog-generator/github-changelog-generator) automates changelog creation. A new Python-based changelog generation tool is needed that parses Git commit messages following the Conventional Commits specification, categorizes changes, determines the next semantic version, and generates a changelog in Keep a Changelog format — enabling automated release note generation from commit history.

## Files to Create/Modify

- `lib/changelog/commit_parser.py` (create) — Parses Conventional Commit messages into structured objects
- `lib/changelog/version_calculator.py` (create) — Determines the next semantic version based on commit types
- `lib/changelog/generator.py` (create) — Generates changelog markdown from parsed commits
- `lib/changelog/git_log.py` (create) — Reads Git log entries from a repository
- `lib/changelog/__init__.py` (create) — Package init
- `tests/test_changelog_automation.py` (create) — Tests for parsing, versioning, and generation

## Requirements

### Commit Parser

- `parse_commit(message: str) -> ConventionalCommit` — parses a single commit message
- `ConventionalCommit` fields: `type` (str), `scope` (str or None), `description` (str), `body` (str or None), `breaking` (bool), `footers` (dict[str, str])
- Must parse the full Conventional Commits format: `<type>[optional scope][!]: <description>\n\n[optional body]\n\n[optional footer(s)]`
- Breaking changes detected by: (1) `!` after type/scope, or (2) `BREAKING CHANGE:` or `BREAKING-CHANGE:` in footer
- Invalid commit messages (not matching the format) must return `None`, not raise an error
- Type must be one of: `feat`, `fix`, `docs`, `style`, `refactor`, `perf`, `test`, `chore`, `ci`, `build`, `revert`

### Version Calculator

- `calculate_next_version(current_version: str, commits: list[ConventionalCommit]) -> str` — determines the next semver based on commits since the last release
- Rules:
  - Any `breaking` commit → bump MAJOR
  - Any `feat` commit → bump MINOR (if no MAJOR bump)
  - Any `fix` commit → bump PATCH (if no MINOR or MAJOR bump)
  - No relevant commits → no version bump (return current version)
- `current_version` must follow semver format `X.Y.Z`; otherwise raise `ValueError`
- Pre-release versions (e.g., `1.0.0-beta.1`) must be handled: a bump from pre-release goes to the release version (e.g., `1.0.0-beta.1` → `1.0.0` for a fix)

### Changelog Generator

- `generate_changelog(version: str, date: str, commits: list[ConventionalCommit], repo_url: str = None) -> str` — produces markdown for a single version entry
- Mapping from commit type to section:
  - `feat` → `### Added`
  - `fix` → `### Fixed`
  - `perf` → `### Changed`
  - `refactor` → `### Changed`
  - `revert` → `### Removed`
  - `docs`, `style`, `test`, `chore`, `ci`, `build` → excluded from changelog
- Breaking changes appear in a separate `### BREAKING CHANGES` section at the top regardless of their type
- Each entry formatted as: `- <description> (<scope>)` if scope present, otherwise `- <description>`
- Sections must appear in order: BREAKING CHANGES, Added, Changed, Deprecated, Removed, Fixed, Security
- Empty sections must be omitted
- If `repo_url` is provided, include a comparison link at the bottom: `[<version>]: <repo_url>/compare/v<prev>...v<version>`

### Full Changelog Assembly

- `generate_full_changelog(releases: list[dict]) -> str` — produces a complete changelog file with header, all releases, and an Unreleased section
- Each release dict: `{"version": str, "date": str, "commits": list[ConventionalCommit]}`
- Header: `# Changelog\n\nAll notable changes to this project will be documented in this file.\n\nThe format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),\nand this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).`

### Expected Functionality

- Parsing `"feat(auth): add OAuth2 login support"` returns type=feat, scope=auth, description="add OAuth2 login support", breaking=False
- Parsing `"fix!: resolve crash on empty input"` returns type=fix, breaking=True
- Given current version `1.2.3` and commits `[feat, fix, fix]`, next version is `1.3.0`
- Given current version `1.2.3` and a breaking change, next version is `2.0.0`
- Generating changelog for version `1.3.0` with 1 feat and 2 fixes produces sections `### Added` and `### Fixed`
- Commits of type `docs`, `test`, `chore` do not appear in the generated changelog

## Acceptance Criteria

- Commit parser correctly handles all Conventional Commit formats including scope, breaking indicator, body, and footers
- Invalid commit messages return `None` instead of raising
- Version calculator correctly bumps MAJOR/MINOR/PATCH based on commit types and breaking changes
- Changelog generator produces valid Keep a Changelog markdown with correct section ordering
- Breaking changes are highlighted in a dedicated section regardless of commit type
- Non-user-facing commit types (docs, test, chore, ci, build, style) are excluded from the changelog
- Full changelog assembly includes header, unreleased section, and all releases in reverse chronological order
- Tests cover parsing, versioning edge cases, and generation output
