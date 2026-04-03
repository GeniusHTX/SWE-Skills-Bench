# Task: Implement Automated Changelog Generation from Git History

## Background

github-changelog-generator (https://github.com/github-changelog-generator/github-changelog-generator) is a Ruby tool that generates changelogs from GitHub repositories. This task requires building a Ruby module that extends the generator with a custom changelog formatter supporting Conventional Commits, auto-categorization of changes, SemVer version inference, and Markdown output with configurable sections.

## Files to Create/Modify

- `lib/github_changelog_generator/conventional_parser.rb` (create) — Parser that extracts Conventional Commit metadata (type, scope, breaking flag, description) from commit messages. Recognizes types: `feat`, `fix`, `docs`, `style`, `refactor`, `perf`, `test`, `build`, `ci`, `chore`.
- `lib/github_changelog_generator/categorizer.rb` (create) — Categorizer that groups parsed commits into changelog sections: "Features" (feat), "Bug Fixes" (fix), "Performance" (perf), "Breaking Changes" (any with `!` or `BREAKING CHANGE` footer), "Documentation" (docs), "Other" (remaining types).
- `lib/github_changelog_generator/version_inferrer.rb` (create) — SemVer version inferrer: given the current version and a list of categorized commits, determines the next version. Breaking changes → major bump, features → minor bump, fixes → patch bump. Supports pre-release labels.
- `lib/github_changelog_generator/markdown_formatter.rb` (create) — Markdown formatter: generates a changelog entry for a version with sections for each category, commit descriptions with PR/issue links, contributor attribution, and formatted dates.
- `spec/conventional_parser_spec.rb` (create) — RSpec tests for the parser.
- `spec/categorizer_spec.rb` (create) — RSpec tests for the categorizer.
- `spec/version_inferrer_spec.rb` (create) — RSpec tests for version inference.
- `spec/markdown_formatter_spec.rb` (create) — RSpec tests for Markdown output.

## Requirements

### Conventional Commit Parser

- Parse messages matching the pattern: `type(scope)!: description` where `(scope)` and `!` are optional.
- Extract: `type` (string), `scope` (string or nil), `breaking` (boolean — true if `!` present or body contains `BREAKING CHANGE:`), `description` (string).
- Multi-line messages: the first line is the subject; scan the body for `BREAKING CHANGE: <description>` footer.
- Non-conventional commits (no matching pattern) → categorize as type `other` with the full message as description.

### Categorizer

- `Categorizer.new(commit_list)` — accepts array of parsed commit objects.
- `categorize()` → returns a hash mapping section names to arrays of commits:
  - `"Features"` ← `feat`
  - `"Bug Fixes"` ← `fix`
  - `"Performance Improvements"` ← `perf`
  - `"Breaking Changes"` ← any commit with `breaking: true`
  - `"Documentation"` ← `docs`
  - `"Maintenance"` ← `build`, `ci`, `chore`, `refactor`, `style`, `test`
  - `"Other"` ← `other`
- Commits with `breaking: true` appear in BOTH their primary category and "Breaking Changes".
- Empty categories are omitted from the output.

### Version Inferrer

- `VersionInferrer.new(current_version)` — takes a SemVer string like `"1.2.3"`.
- `infer(categories)` → returns the next version string:
  - If "Breaking Changes" non-empty → bump major: `"1.2.3" → "2.0.0"`.
  - Else if "Features" non-empty → bump minor: `"1.2.3" → "1.3.0"`.
  - Else → bump patch: `"1.2.3" → "1.2.4"`.
- Support pre-release: `infer(categories, pre_release: "beta")` → `"2.0.0-beta.1"`.
- Handle version at `"0.x.y"`: in 0.x, breaking changes bump minor, features bump patch (SemVer 0.x convention).

### Markdown Formatter

- `MarkdownFormatter.new(version, date, categories, options)`.
- `format()` → Markdown string:
```markdown
## [1.3.0](https://github.com/owner/repo/compare/v1.2.3...v1.3.0) (2024-01-15)

### Breaking Changes

- **auth**: remove deprecated OAuth1 support ([#142](https://github.com/owner/repo/pull/142))

### Features

- **api**: add batch processing endpoint ([#138](https://github.com/owner/repo/pull/138))

### Bug Fixes

- **parser**: handle empty input gracefully ([#140](https://github.com/owner/repo/pull/140))
```
- Each entry: `- **{scope}**: {description} ([#{pr_number}](url))` or `- {description}` if no scope.
- Options: `repo_url` (for links), `include_contributors` (boolean), `include_compare_link` (boolean).

### Expected Functionality

- `ConventionalParser.parse("feat(api)!: add streaming support")` → `{type: "feat", scope: "api", breaking: true, description: "add streaming support"}`.
- `ConventionalParser.parse("fixed the login bug")` → `{type: "other", scope: nil, breaking: false, description: "fixed the login bug"}`.
- `VersionInferrer.new("1.2.3").infer(categories_with_breaking)` → `"2.0.0"`.
- `VersionInferrer.new("0.5.2").infer(categories_with_breaking)` → `"0.6.0"` (0.x convention).

## Acceptance Criteria

- The parser correctly extracts type, scope, breaking flag, and description from Conventional Commit messages.
- Non-conventional commits are gracefully handled as type `other`.
- The categorizer groups commits into correct sections and includes breaking changes in both their primary category and "Breaking Changes".
- Version inferrer follows SemVer rules including the 0.x exception and pre-release support.
- Markdown formatter produces correctly structured output with sections, scope-prefixed entries, and PR links.
- All RSpec tests pass: `bundle exec rspec spec/`.
