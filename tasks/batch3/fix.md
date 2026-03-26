# Task: Fix Lint and Formatting Errors in the Upgradle React Application

## Background

The Upgradle application (https://github.com/michaelasper/upgradle) is a React-based web application. The codebase has accumulated formatting inconsistencies and lint violations that cause CI pipeline failures. All formatting and lint issues need to be resolved so the codebase passes automated checks cleanly.

## Files to Create/Modify

- `src/**/*.{js,jsx,ts,tsx}` (modify) — Fix formatting issues across all source files
- `package.json` (modify if needed) — Ensure lint and format scripts are correctly configured

## Requirements

### Formatting

- All JavaScript/TypeScript files must conform to the project's Prettier configuration
- Run the project's formatting command and commit the results
- Ensure no formatting-only changes are mixed with logic changes

### Lint Violations

- All ESLint violations must be resolved
- Fix actual code issues (unused imports, missing dependencies in hooks, etc.) rather than disabling rules
- For any rule that truly cannot be satisfied without breaking functionality, add a targeted inline disable comment with an explanation — do not add blanket rule disables in config files

### Verification

- After all fixes, the project's lint command must exit with code 0
- After all fixes, the project's format-check command must exit with code 0
- No new warnings should be introduced

### Expected Functionality
- `yarn prettier --check .` exits with code 0 (all files formatted)
- `yarn linc` exits with code 0 (all lint checks pass)

- `npm run prettier -- --check .` exits with code 0 (all files formatted)
- `npm run lint` exits with code 0 (all lint checks pass). Tests may accept a `linc` alias, but CI uses `npm run lint`.
- The application still builds and renders correctly after fixes
- No functional behavior changes — only formatting and lint fixes

CI note: prefer installing dependencies with `npm ci` (or `npm install` as fallback) so `node_modules` contains devDependencies like `prettier`, `eslint`, and `vite` required for checks and builds.

## Acceptance Criteria

- All source files pass Prettier formatting checks with zero differences
- All source files pass ESLint with zero errors
- The application builds successfully after all fixes
- No ESLint rules are globally disabled in configuration files
- Any inline rule disables include a comment explaining why the disable is necessary
