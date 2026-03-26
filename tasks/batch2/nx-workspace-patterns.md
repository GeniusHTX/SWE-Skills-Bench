# Task: Validate Nx Affected Task Graph Resolution

## Background

Nx (https://github.com/nrwl/nx) is a monorepo build system with intelligent task scheduling. The project needs additional verification that the `nx affected` command correctly resolves dependency graphs and identifies which projects need to be rebuilt when specific files change.

## Files to Create/Modify

- `e2e/nx/src/affected-graph.test.ts` (create) — E2E test validating affected task graph resolution
- `e2e/nx/src/fixtures/affected-demo/workspace.json` (create) — Multi-project workspace fixture with inter-project dependencies

## Requirements

### Workspace Structure

- Define or extend a multi-project workspace with clear inter-project dependency relationships
- Include at least three projects: a shared library, an application depending on it, and an independent project

### Affected Graph Testing

- Demonstrate that modifying a file in the shared library marks both the library and the dependent application as affected, but not the independent project
- Verify that the task execution order respects the dependency graph (library builds before application)
- Test that modifying a file only in the independent project does not trigger rebuilds of other projects

### Build Verification

- All workspace projects must build successfully
- The Nx task graph must resolve without circular dependency errors

## Expected Functionality

- The affected mechanism correctly identifies impacted projects based on file changes
- Task execution respects the topological ordering of the dependency graph
- Independent projects remain unaffected by changes in unrelated projects

## Acceptance Criteria

- The workspace fixture contains at least one shared library, one dependent application, and one unrelated project.
- A change in the shared library marks both the library and its dependent application as affected, but not the unrelated project.
- A change in the unrelated project does not trigger rebuilds for the shared library or dependent application.
- The execution order of affected tasks follows the project dependency graph.
- The workspace configuration avoids circular dependency behavior while still demonstrating affected-graph resolution clearly.
