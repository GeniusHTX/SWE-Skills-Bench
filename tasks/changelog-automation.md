# Task: Add GitHub Changelog Generator Configuration Example

## Background
   Add a complete changelog generation
   configuration example demonstrating the github-changelog-generator
   tool's capabilities and customization options.

## Files to Create/Modify
   - examples/advanced_config/.github_changelog_generator (configuration)
   - examples/advanced_config/CHANGELOG.md (sample output)
   - examples/advanced_config/README.md (documentation)

## Requirements
   
   Configuration File (.github_changelog_generator):
   - user and project settings
   - since_tag and due_tag options
   - issue/PR label filtering
   - Section customization (enhancement, bug, etc.)
   
   Label Configuration:
   - enhancement-labels: ["enhancement", "feature"]
   - bug-labels: ["bug", "fix"]
   - breaking-labels: ["breaking-change"]
   - exclude-labels: ["duplicate", "wontfix"]
   
   Output Formatting:
   - Custom header template
   - Date format configuration
   - Compare URL inclusion
   - Unreleased section handling

4. Configuration Options to Demonstrate:
   - unreleased: true/false
   - base: HISTORY.md (optional base file)
   - header: Custom header text
   - include_labels: Label filtering
   - breaking_prefix: "**Breaking Changes:**"

## Acceptance Criteria
   - Configuration file is valid and parseable
   - README explains each configuration option
   - `github_changelog_generator --config examples/advanced_config/.github_changelog_generator --help` validates
