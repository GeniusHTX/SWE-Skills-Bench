# Task: Fix Linting and Formatting Errors in Upgradle React Application

## Background

The Upgradle repository (https://github.com/michaelasper/upgradle) is a React application that has accumulated linting and formatting violations across its components. The CI pipeline runs Prettier for formatting and a linter (via `yarn linc`) for code quality checks, and both are currently failing. All formatting and lint errors must be resolved so the CI pipeline passes.

## Files to Create/Modify

- `src/App.tsx` (modify) — Fix formatting inconsistencies and lint errors
- `src/components/Board.tsx` (modify) — Fix formatting, unused imports, and lint violations
- `src/components/Tile.tsx` (modify) — Fix formatting and lint errors
- `src/components/Keyboard.tsx` (modify) — Fix formatting, unused variables, and lint violations
- `src/utils/game.ts` (modify) — Fix formatting and lint errors in game logic utilities
- `src/utils/words.ts` (modify) — Fix formatting issues

## Requirements

### Formatting (Prettier)

- All `.tsx`, `.ts`, `.css`, and `.json` files must conform to the project's Prettier configuration.
- Fix all inconsistent indentation (tabs vs. spaces mismatches).
- Fix all trailing comma violations — ensure trailing commas match the Prettier config setting.
- Fix all quote style violations — ensure consistent single or double quotes per the project configuration.
- Fix all line length violations where Prettier would rewrap.
- Fix all missing or extra semicolons per the Prettier config.

### Lint Errors

- Remove all unused import statements (imports that are declared but never referenced in the file).
- Remove all unused variable declarations (variables assigned but never read).
- Fix all missing React key prop warnings in `.map()` JSX renders — every dynamically rendered element must have a unique `key` prop.
- Fix all uses of `any` type where a more specific type can be inferred from context.
- Fix all missing return type annotations on exported functions if required by the linter configuration.
- Ensure no `console.log` statements remain in production code (move to conditional debug logging or remove).

### Expected Functionality

- Running `yarn prettier` produces zero formatting changes (all files already formatted).
- Running `yarn linc` produces zero lint errors and zero warnings.
- The application still builds and runs correctly after all fixes — no behavioral changes are introduced.
- Existing game logic (word validation, board state, keyboard coloring) continues to function identically.

## Acceptance Criteria

- `yarn prettier` reports no files need formatting changes.
- `yarn linc` exits with code 0 and reports no errors.
- No unused imports or unused variables remain in any source file.
- All JSX list renders include a unique `key` prop.
- The application builds without errors and the game plays correctly in a browser.
- No functional logic has been changed — only formatting, imports, variable declarations, and type annotations are modified.
