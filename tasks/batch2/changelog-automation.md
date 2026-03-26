# Task: Add Changelog Generation Configuration to github-changelog-generator

## Background

The github-changelog-generator project (https://github.com/github-changelog-generator/github-changelog-generator) automates changelog creation from GitHub data. A complete configuration example is needed that demonstrates the tool's configuration options for different release workflows, including section customization, label mapping, and output formatting.

## Files to Create/Modify

- `lib/github_changelog_generator/section_config.rb` (create) — Section configuration class with label-to-section mapping
- `lib/github_changelog_generator/formatter/keep_a_changelog.rb` (create) — Keep a Changelog output formatter
- `.github_changelog_generator` (create) — Configuration file with label mappings, inclusion/exclusion rules, and output settings

## Requirements

### Configuration

- Define a configuration that maps GitHub label names to changelog sections (e.g., `enhancement` → "Features", `bug` → "Bug Fixes", `breaking` → "Breaking Changes")
- Configure inclusion/exclusion rules for PRs and issues
- Set up header formatting, date format, and version tag patterns

### Section Customization

- Support at least four distinct changelog sections with custom headings
- Configure the ordering of sections in the output
- Handle unlabeled items by placing them in a default section

### Output Format

- Generate output following the Keep a Changelog format
- Include links to PR/issue URLs and contributor attribution
- Support both Markdown and plain text output

### Ruby Integration

- Code under `lib/` must pass Ruby syntax checking
- Follow the project's existing coding conventions

## Expected Functionality

- Running the generator with the new configuration produces a well-structured changelog
- PRs are correctly categorized into their configured sections
- Output follows Keep a Changelog formatting conventions

## Acceptance Criteria

- The changelog configuration maps labels into clearly separated output sections such as features, bug fixes, and breaking changes.
- Unlabeled items are placed into a defined fallback section rather than being lost or miscategorized.
- Generated output follows a Keep a Changelog style structure and includes links to relevant issues or pull requests.
- Both configuration and formatter behavior support predictable section ordering and heading customization.
- The solution can produce either Markdown output or plain-text output from the same release metadata.
