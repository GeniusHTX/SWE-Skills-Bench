# Task: Fix Lint and Formatting Errors in Upgradle

## Background

The Upgradle repository (a Vite + React + TypeScript word-guessing game) has accumulated formatting inconsistencies and lint violations that cause CI to fail. The codebase uses Prettier for code formatting and ESLint (via the `yarn linc` script) for static analysis. All formatting and lint errors must be resolved so that CI passes cleanly.

## Files to Create/Modify

- `src/App.tsx` (modify) — Fix formatting and lint violations in the main application component
- `src/dictionary.ts` (modify) — Fix formatting issues in the dictionary module
- `eslint.config.js` (modify) — Fix any formatting inconsistencies in the ESLint configuration itself
- `package.json` (modify) — Ensure `prettier` and `linc` scripts are present and correct

## Requirements

### Formatting Compliance

- All `.ts`, `.tsx`, `.js`, and `.json` files in the project must conform to the Prettier configuration defined in the repository
- Run the project's Prettier script (`yarn prettier`) which formats only changed files tracked by version control
- Trailing whitespace, inconsistent indentation, missing trailing commas, incorrect quote styles, and line-length violations must all be resolved

### Lint Compliance

- All files must pass ESLint analysis as executed by `yarn linc`
- Unused imports in `src/App.tsx` and other source files must be removed
- Any variables declared but never read must be either used or removed
- React hook dependency arrays must be complete and correct — missing dependencies flagged by `react-hooks/exhaustive-deps` must be addressed
- TypeScript `@ts-ignore` comments that suppress valid errors must be replaced with proper type annotations or type guards

### No Functional Regressions

- Fixes must be limited to formatting and lint compliance; application logic, component behavior, and game mechanics must remain unchanged
- Do not rename public-facing identifiers or restructure modules beyond what is required to resolve lint violations

### Expected Functionality

- `yarn prettier` exits with code 0 and reports no remaining formatting differences
- `yarn linc` exits with code 0 and reports zero warnings and zero errors
- `yarn build` (Vite production build) succeeds without type errors or build failures
- The application renders and functions identically to its pre-fix state

## Acceptance Criteria

- `yarn prettier` produces no formatting diffs when run a second time (idempotent)
- `yarn linc` exits with code 0 reporting zero errors and zero warnings
- `yarn build` completes successfully with exit code 0
- No application logic, component props, or game-rule behavior has been altered by the fixes
