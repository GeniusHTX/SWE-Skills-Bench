# Task: Add Conventional Commits Parsing and Scoped Changelog Generation to github-changelog-generator

## Background

github-changelog-generator (https://github.com/github-changelog-generator/github-changelog-generator) is a Ruby tool that generates changelogs from GitHub pull requests and issues. The task is to extend it with Conventional Commits support — parsing commit messages that follow the `type(scope): description` format, grouping changes by type and scope, and generating structured changelog sections with breaking change detection.

## Files to Create/Modify

- `lib/github_changelog_generator/parser/conventional_commit_parser.rb` (create) — Parser for Conventional Commits format that extracts type, scope, description, body, and breaking change indicators
- `lib/github_changelog_generator/generator/scoped_changelog.rb` (create) — Changelog generator that groups parsed commits by type and scope, producing structured Markdown output
- `lib/github_changelog_generator/parser/conventional_commit_parser_test.rb` (create) — Tests for the commit parser
- `spec/unit/generator/scoped_changelog_spec.rb` (create) — RSpec tests for the scoped changelog generator

## Requirements

### `ConventionalCommitParser` (`conventional_commit_parser.rb`)

#### `ConventionalCommit` struct/class
```ruby
class ConventionalCommit
  attr_reader :type, :scope, :description, :body, :breaking, :breaking_description,
              :footers, :raw_message, :sha, :author, :date

  # type: "feat", "fix", "docs", "style", "refactor", "perf", "test", "build", "ci", "chore", "revert"
  # scope: optional, e.g., "auth", "api", "parser"
  # breaking: boolean, true if "!" suffix or "BREAKING CHANGE:" footer
  # footers: hash of footer key => value (e.g., {"Reviewed-by" => "Alice", "Refs" => "#123"})
end
```

#### `parse(commit_message, sha: nil, author: nil, date: nil) -> ConventionalCommit | nil`
- Parse a commit message following the format: `type(scope)!: description`
- The regex pattern: `^(?<type>\w+)(\((?<scope>[^)]+)\))?(?<breaking>!)?:\s+(?<description>.+)$` for the first line
- Parse the body (second paragraph onwards, separated by blank line from the subject)
- Parse footers from the body: lines matching `^(?<key>[\w-]+|BREAKING CHANGE):\s+(?<value>.+)$` or `^(?<key>[\w-]+|BREAKING CHANGE)\s+#(?<value>.+)$`
- A commit is breaking if: the subject has `!` before `:`, OR there is a `BREAKING CHANGE:` footer
- If `breaking_description` is not explicitly provided, use the commit description
- Return `nil` if the message doesn't match Conventional Commits format
- Supported types: `feat`, `fix`, `docs`, `style`, `refactor`, `perf`, `test`, `build`, `ci`, `chore`, `revert`
- Unknown types are accepted but flagged with `type_known? == false`

#### `parse_all(commits) -> Array<ConventionalCommit>`
- Takes an array of raw commit hashes `{message:, sha:, author:, date:}` and returns parsed `ConventionalCommit` objects
- Non-conforming messages are silently skipped (return only successfully parsed commits)

### `ScopedChangelog` (`scoped_changelog.rb`)

#### Constructor
```ruby
class ScopedChangelog
  def initialize(commits, options = {})
    # commits: Array<ConventionalCommit>
    # options:
    #   version: "1.2.0" (version string for the heading)
    #   date: "2024-01-15" (release date)
    #   repository_url: "https://github.com/org/repo"
    #   group_by: :type (default) or :scope
    #   include_types: ["feat", "fix", "perf", "refactor"] (types to include; default: all)
    #   exclude_types: ["chore", "ci", "style"] (types to exclude; overridden by include_types)
    #   show_authors: true/false (default: false)
    #   show_sha: true/false (default: true)
    #   compare_url: "https://github.com/org/repo/compare/v1.1.0...v1.2.0" (optional)
  end
```

#### `generate -> String`

Produces a Markdown changelog string with the following structure:

```markdown
## [1.2.0](https://github.com/org/repo/compare/v1.1.0...v1.2.0) (2024-01-15)

### ⚠ BREAKING CHANGES

* **auth:** Users must re-authenticate after upgrade ([abc1234](https://github.com/org/repo/commit/abc1234))

### Features

* **api:** Add bulk import endpoint ([def5678](https://github.com/org/repo/commit/def5678))
* **auth:** Add OAuth2 support ([abc1234](https://github.com/org/repo/commit/abc1234))

### Bug Fixes

* **parser:** Fix UTF-8 handling in CSV parser ([ghi9012](https://github.com/org/repo/commit/ghi9012))
* Fix crash on empty input ([jkl3456](https://github.com/org/repo/commit/jkl3456))

### Performance Improvements

* **db:** Optimize query for large datasets ([mno7890](https://github.com/org/repo/commit/mno7890))
```

#### Grouping Rules

- **Breaking changes** always appear first in their own section, regardless of type
- Type-to-heading mapping:
  - `feat` → `Features`
  - `fix` → `Bug Fixes`
  - `perf` → `Performance Improvements`
  - `refactor` → `Code Refactoring`
  - `docs` → `Documentation`
  - `test` → `Tests`
  - `build` → `Build System`
  - `ci` → `Continuous Integration`
  - `revert` → `Reverts`
  - `chore` → `Chores`
  - `style` → `Styles`
- Within each type section, commits are sorted by scope (alphabetically), then by date
- Commits without a scope appear after scoped commits within the same type section
- If `group_by: :scope`, the primary grouping is by scope instead of type

#### Formatting

- Each entry: `* **scope:** description ([sha_short](commit_url))` — if scope exists
- Without scope: `* description ([sha_short](commit_url))`
- If `show_authors: true`, append ` (@author)` to each entry
- SHA is truncated to first 7 characters in display
- If `show_sha: false`, omit the commit link

## Expected Functionality

- Parsing `"feat(auth): add OAuth2 login support"` produces a `ConventionalCommit` with `type: "feat"`, `scope: "auth"`, `description: "add OAuth2 login support"`, `breaking: false`
- Parsing `"fix!: correct null pointer in parser"` produces `breaking: true`, `scope: nil`
- Parsing `"feat(api): new endpoint\n\nBREAKING CHANGE: /v1/users removed"` produces `breaking: true`, `breaking_description: "/v1/users removed"`
- Generating a changelog from 10 mixed commits produces sections ordered: Breaking Changes, Features, Bug Fixes, etc.

## Acceptance Criteria

- `ConventionalCommitParser.parse` correctly extracts type, scope, description, body, footers, and breaking status
- Breaking changes are detected via both `!` suffix and `BREAKING CHANGE:` footer
- Non-conforming commit messages return `nil` from `parse`
- `ScopedChangelog.generate` produces valid Markdown with proper heading hierarchy
- Breaking changes appear in a dedicated section before all type sections
- Commits are grouped by type (or scope), sorted alphabetically by scope within each group
- Type filtering via `include_types` / `exclude_types` works correctly
- SHA links point to the correct commit URL using the repository_url
- All RSpec tests pass covering parsing edge cases and changelog formatting
