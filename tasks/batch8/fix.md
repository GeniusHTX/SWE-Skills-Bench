# Task: Fix Lint and Formatting Violations in the Upgradle React/TypeScript Project

## Background

Upgradle (https://github.com/michaelasper/upgradle, commit `5f292188`) is a Wordle-style word game built with React, TypeScript, and Vite. The codebase has accumulated ESLint errors and Prettier formatting inconsistencies that cause CI checks to fail. All lint and formatting violations must be resolved so the project passes its automated code-quality gates.

## Files to Create/Modify

- `src/App.tsx` (modify) — Main application component; fix ESLint errors (unused variables, missing dependencies in hooks, type issues) and Prettier formatting violations
- `src/dictionary.ts` (modify) — Word dictionary module; fix any formatting inconsistencies
- `src/App.css` (modify) — Stylesheet; fix Prettier formatting if needed
- `src/index.css` (modify) — Global stylesheet; fix Prettier formatting if needed
- `eslint.config.js` (modify, if needed) — ESLint configuration; do not weaken rules to suppress genuine errors

## Requirements

### ESLint Error Resolution

- All ESLint errors reported by `yarn linc` must be resolved by fixing the source code, not by adding `eslint-disable` comments or weakening rule configuration
- Unused variable declarations must be removed or prefixed with an underscore if they are required by a function signature
- React hook dependency arrays must be corrected to include all referenced variables, or the code must be restructured to eliminate the dependency
- TypeScript type errors flagged by ESLint (e.g., `@typescript-eslint/no-unused-vars`, `@typescript-eslint/no-explicit-any`) must be resolved with proper type annotations
- Any `==` comparisons must be replaced with `===` if flagged by the linter

### Prettier Formatting

- All source files must conform to the project's Prettier configuration
- Formatting must be applied using the project's own Prettier setup (`yarn prettier`), not an external or default Prettier configuration
- Indentation, trailing commas, semicolons, quote style, and line length must match the project's `.prettierrc` or Prettier config in `package.json`

### Code Correctness Constraints

- Fixes must not change the game's runtime behavior — the app must still function identically after all lint/formatting changes
- No new dependencies may be added to resolve lint issues
- JSX structure and component hierarchy must remain semantically equivalent; only formatting and lint-related code changes are permitted

## Expected Functionality

- Running `yarn prettier` produces no formatting changes (all files already correctly formatted)
- Running `yarn linc` reports zero ESLint errors and zero warnings
- The application starts with `yarn dev` and the Wordle-style game is fully playable with no console errors
- The existing E2E tests in `tests/e2e/` continue to pass

## Acceptance Criteria

- `yarn linc` exits with code 0 and produces no error output
- `yarn prettier` reports no files that would be reformatted (i.e., `--check` mode passes)
- The application builds successfully with `yarn build` and produces no TypeScript compilation errors
- No `eslint-disable` comments have been added to suppress errors
- No ESLint rules have been disabled or downgraded in `eslint.config.js`
- The game's functional behavior is unchanged — all existing E2E tests pass
