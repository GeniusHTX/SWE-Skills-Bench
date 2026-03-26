# Task: Fix Lint and Formatting Violations in a React TypeScript Project

## Background

The Upgradle project (https://github.com/michaelasper/upgradle) is a React-based TypeScript application. The codebase has accumulated lint errors and formatting inconsistencies that block the CI pipeline. All violations need to be resolved so the project meets its established code quality standards.

## Files to Modify

- `src/App.tsx` — Main application component
- `src/index.tsx` — Application entry point
- All additional `.ts` and `.tsx` files under `src/` that report lint or formatting violations (run `npm run lint` to enumerate the full list)

## Requirements

- Run the project's lint toolchain and identify all reported violations
- Fix each violation in-place — do not suppress errors with inline disable comments unless absolutely necessary
- Preserve the original behavior and logic of the code; only change formatting, style, and lint compliance
- Ensure all auto-fixable issues are resolved first, then address remaining manual fixes
- Do not introduce new dependencies or alter the project's lint/prettier configuration

## Expected Functionality

- The project's lint command runs cleanly with zero errors
- All source files conform to the project's ESLint and Prettier configuration
- No functional changes are introduced

## Acceptance Criteria

- The project no longer contains outstanding lint or formatting violations in the files addressed by the task.
- Fixes preserve the existing application behavior and do not introduce feature changes.
- Auto-fixable issues are resolved cleanly and any remaining manual fixes follow the repository's existing code style.
- No lint rule is bypassed through blanket disable comments or configuration weakening.
- The resulting codebase is consistent with the existing ESLint and formatting conventions.
