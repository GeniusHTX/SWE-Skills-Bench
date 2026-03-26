# Task: Fix ESLint Violations in TypeScript Codebase

## Background

The upgradle project uses TypeScript + ESLint for code quality enforcement. Currently, the `src/` directory contains multiple ESLint rule violations that need to be addressed:

- `no-unused-vars`
- `@typescript-eslint/no-explicit-any`
- `eqeqeq` (strict equality)

## Objective

Scan and fix all lint errors in `.ts` files under the `src/` directory to ensure the codebase passes linting checks.

## Scope

- **Files to modify**: `src/**/*.ts` (all TypeScript files in src directory)
- **Files to preserve**: Do NOT modify any test files

- **Repo requirements**: Ensure a `package.json` exists with `lint` and `test` scripts and a `src/` directory containing one or more `.ts` files so the test harness can run.

## Requirements

- Fix all ESLint error-level violations
- Maintain existing functionality (all existing tests must continue to pass)
- Follow TypeScript best practices
- Replace `any` types with proper type definitions where possible
- Use strict equality (`===`) instead of loose equality (`==`)
- Remove or properly use unused variables

## Acceptance Criteria

- `npm run lint` exits with code 0 (no error-level reports)

- No new lint warnings introduced
