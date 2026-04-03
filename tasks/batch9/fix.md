# Task: Fix Lint and Formatting Errors in Upgradle React Application

## Background

The Upgradle application (https://github.com/michaelasper/upgradle) is a Wordle-variant game built with React, TypeScript, and Vite. The codebase currently has lint errors reported by ESLint and formatting inconsistencies that would cause CI failures. These issues span the main application component, the dictionary utility module, and the Vite/TypeScript configuration files.

## Files to Create/Modify

- `src/App.tsx` (modify) — Fix lint errors in the main React component (unused variables, missing dependencies in hooks, type issues)
- `src/dictionary.ts` (modify) — Fix lint warnings in the dictionary filtering module
- `eslint.config.js` (modify) — Ensure ESLint configuration is consistent and all rules resolve correctly
- `vite.config.ts` (modify) — Fix any formatting inconsistencies in the Vite configuration

## Requirements

### Lint Error Resolution

- All errors reported by the project's ESLint configuration (`eslint.config.js`) must be resolved
- Unused variable declarations in `src/App.tsx` must be removed or prefixed with an underscore if required by a destructuring pattern
- React hook dependency arrays must include all referenced variables from the enclosing scope; missing dependencies flagged by `react-hooks/exhaustive-deps` must be corrected without introducing infinite re-render loops
- TypeScript type errors flagged by `@typescript-eslint/*` rules must be fixed with proper type annotations or type guards, not `any` casts

### Formatting Consistency

- All `.ts` and `.tsx` files must conform to the project's Prettier configuration
- Indentation, trailing commas, semicolons, and quote style must be uniform across the codebase
- No file may mix tabs and spaces

### Behavioral Preservation

- The game logic in `src/App.tsx` — including the reducer, hint calculation, guess validation, and win/loss detection — must behave identically before and after the fixes
- The dictionary filtering logic in `src/dictionary.ts` must return the same word lists for the same inputs
- No runtime behavior may change; fixes are limited to static analysis and formatting

### Expected Functionality

- Running the lint check produces zero errors and zero warnings
- Running the formatter in check mode reports no differences
- The application starts via `npm run dev` and the game plays correctly in a browser

## Acceptance Criteria

- The ESLint check (`npx eslint .`) exits with code 0 and produces no error-level or warning-level diagnostics
- The Prettier check (`npx prettier --check .`) exits with code 0, confirming all files are formatted
- The TypeScript compiler (`npx tsc --noEmit`) exits with code 0
- The application builds without errors (`npm run build`)
- Existing Playwright end-to-end tests in `tests/e2e/` pass without modification
