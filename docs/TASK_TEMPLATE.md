# Task File Template

This document provides a standardized template for creating task files that align with skills and repositories.

## Template Structure

# Task: [Verb] [Feature/Thing]

## Background

[1-3 sentences explaining what needs to be done and why. Reference the repository context.]

## Objective

<!-- Optional: include when Background alone is insufficient to convey the goal -->

[Clear statement of what the agent should produce or accomplish.]

## Files to Create/Modify

- `path/to/new_file.ext` - Description of what goes here (new)
- `path/to/existing_file.ext` - What to add/change (modify)
- `path/to/another_file.ext` - Additional file when the task needs more than one concrete change location

## Requirements

### [Category 1 — e.g. Class / API / Schema]

- Requirement 1
- Requirement 2

### [Category 2 — e.g. Behavior / Logic / Config]

- Requirement 3
- Requirement 4

### Expected Functionality

- Scenario 1 → expected outcome
- Scenario 2 → expected outcome
- Edge case → graceful handling

## Acceptance Criteria

- API or CLI behavior matches the required output and error-handling expectations
- Output contains the expected fields, structure, or generated artifacts
- Invalid inputs are rejected with the expected validation or error behavior
- [Other objectively verifiable criterion]

## Section Guidelines

### `# Task:` Title

- Start with action verb: Add, Implement, Create, Fix, Optimize, Refactor, Design
- Be specific about the feature/functionality
- Match the skill's purpose

### `## Required File Paths` *(optional)*

- Use only when the task must be strictly scoped to specific files
- List each path with a short note on what the agent should do there
- Helps prevent agents from modifying unrelated files

### `## Background`

- 1–3 sentences explaining the problem or need
- Reference the target repository and relevant existing code if applicable
- Avoid implementation details — save those for Requirements

### `## Objective` *(optional)*

- Include when Background alone is not sufficient to convey the specific goal
- One clear statement of the deliverable

### `## Files to Create/Modify`

- Use repository-relative paths
- Append `(new)` or `(modify)` or a short description after each path
- Use concrete file paths, not vague directory-level bullets
- Include test files only when they are natural repository files that the task itself should create or modify

### `## Requirements`

- Break down into logical `###` subsections (e.g., class design, API contract, data schema)
- Include concrete details: class/method names, field types, behavior rules
- Use code blocks for schemas, JSON structures, or SQL
- Add a `### Expected Functionality` subsection listing scenario → outcome pairs
- Do NOT list vague requirements like "the code should work"

### `## Acceptance Criteria`

- Write outcome-based criteria, not raw benchmark commands
- Criteria must be understandable without knowledge of hidden benchmark tests
- Criteria must remain consistent with the evaluation config's intended checks
- Every criterion must be objectively verifiable through behavior, structure, output, or validation outcomes

## Example Acceptance Criteria

### API Feature

```markdown
## Acceptance Criteria
- Endpoint returns the expected status code for valid and invalid requests
- Response body includes the required fields and omits internal-only data
- Authorization rules are enforced for unauthenticated and unauthorized callers
```

### Library / Module

```markdown
## Acceptance Criteria
- The new module exposes the required public API surface
- Valid inputs produce the expected outputs for the documented scenarios
- Invalid inputs fail with clear and predictable error behavior
```

### Configuration / Infra Example

```markdown
## Acceptance Criteria
- The example configuration includes all required resources and environment-specific overrides
- Invalid or incomplete configuration is rejected by the target system's normal validation behavior
- The documented example demonstrates the intended workflow end to end
```

## Anti-Patterns to Avoid

❌ Tasks using wrong technology stack for the repository
❌ Vague validation criteria ("code works correctly", "tests pass")
❌ Acceptance Criteria written as hidden benchmark commands
❌ Directory-only file bullets when concrete file paths can be named
❌ Mixing indented plain-text blocks with Markdown headings inconsistently
