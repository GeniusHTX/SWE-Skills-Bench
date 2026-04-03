# Task: Fix Lint and Formatting Violations in Upgradle React Application

## Background

The Upgradle repository (https://github.com/michaelasper/upgradle) is a React application that enforces code style through Prettier formatting and lint checks in CI. Several source files currently contain formatting inconsistencies and lint violations that cause CI pipeline failures. These must be resolved so the codebase passes automated checks cleanly.

## Files to Create/Modify

- `src/App.js` (modify) — Fix formatting inconsistencies and lint violations
- `src/components/Board.js` (modify) — Fix formatting inconsistencies and lint violations
- `src/components/Tile.js` (modify) — Fix formatting inconsistencies and lint violations
- `src/index.js` (modify) — Fix formatting and unused import warnings

## Requirements

### Formatting Compliance

- All JavaScript/JSX source files under `src/` must conform to the project's Prettier configuration
- Only files that have been changed relative to the main branch should be formatted (the project's formatter is scoped to changed files)
- Indentation, trailing commas, quote style, and line-length wrapping must match the Prettier config in the repository root

### Lint Rule Compliance

- All warnings and errors reported by the project's lint check must be resolved
- Unused variables and unused imports must be removed rather than suppressed with disable comments
- React Hook dependency warnings must be addressed by correcting the dependency arrays, not by adding eslint-disable
- PropTypes declarations must match the actual props used by each component

### No Behavioral Changes

- Fixing formatting and lint issues must not alter the runtime behavior of any component
- Component rendering output, event handlers, and state management must remain functionally identical after the fixes

### Expected Functionality

- Running the project's formatting command produces zero formatting diffs
- Running the project's lint check exits with code 0 and produces no warnings or errors
- The application renders correctly after all fixes are applied
- CI pipeline formatting and lint stages pass

## Acceptance Criteria

- The project's Prettier check reports no formatting differences across all modified files
- The project's lint check completes with zero errors and zero warnings
- No runtime behavior or rendered output is changed by the fixes
- No eslint-disable comments are added to suppress warnings
