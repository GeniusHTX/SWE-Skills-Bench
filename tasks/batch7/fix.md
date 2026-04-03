# Task: Fix Lint and Formatting Errors in the Upgradle React Application

## Background

The Upgradle project (https://github.com/michaelasper/upgradle) is a Wordle-inspired incremental game built with Vite, React, and TypeScript. The codebase currently has lint violations and formatting inconsistencies that prevent the CI workflow from passing. All errors must be resolved so the project passes its automated checks.

## Files to Create/Modify

- `src/App.tsx` (modify) — Fix lint violations and formatting issues in the main application component containing the game reducer, upgrade logic, and UI rendering
- `src/dictionary.ts` (modify) — Fix lint violations in the dictionary module that filters English words to 5–7 letter candidates
- `src/App.css` (modify) — Fix any formatting inconsistencies in the neon-themed stylesheet
- `src/index.css` (modify) — Fix any formatting inconsistencies in the base stylesheet

## Requirements

### Lint Compliance

- All files under `src/` must pass the ESLint configuration defined in `eslint.config.js` with zero errors and zero warnings
- TypeScript-specific lint rules (unused variables, explicit `any` types, missing return types where required) must be resolved
- React-specific lint rules (hooks rules, key props in lists, missing dependencies in effect hooks) must be resolved

### Formatting Compliance

- All source files must conform to the Prettier configuration used by the project
- Indentation, trailing commas, semicolons, quote style, and line length must match the project's formatting standards
- No mixed formatting styles (e.g., some files using single quotes while others use double quotes)

### Functional Preservation

- The game logic in `src/App.tsx` must remain functionally identical after fixes — the Wordle gameplay loop, upgrade system, mint logic, and keyboard input handling must not change behavior
- The dictionary filtering in `src/dictionary.ts` must continue to produce the same set of 5–7 letter word candidates
- No new dependencies may be introduced

### Specific Error Categories to Address

- Unused imports and variables must be removed or used
- Missing `key` props on list-rendered JSX elements must be added
- Type annotations must be corrected where the linter flags them
- Hook dependency arrays must be complete and accurate
- CSS properties must be ordered and formatted per the project's stylelint configuration if applicable

## Expected Functionality

- Running the project lint command produces zero errors and zero warnings
- Running the formatter check produces no diff (all files already formatted)
- The application builds successfully with `npm run build`
- The dev server starts without warnings via `npm run dev`
- Existing E2E tests in `tests/e2e/` continue to pass

## Acceptance Criteria

- The ESLint check exits with code 0 and reports no errors or warnings across all source files
- The Prettier check reports no formatting differences in any source file
- The production build (`npm run build`) completes without errors
- Game functionality is preserved — the Wordle grid, keyboard input, upgrade purchases, and mint mechanics work identically to before the fixes
