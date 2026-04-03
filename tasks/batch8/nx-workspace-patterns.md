# Task: Implement an Nx Project Boundary Enforcement Plugin with Affected Command Support

## Background

Nx provides a plugin system for enforcing workspace conventions and extending the task runner. A new Nx plugin is needed that enforces project boundary rules (preventing unauthorized cross-library imports), generates project tags from directory structure, and provides a custom executor for running affected-only lint checks with caching integration. The plugin targets the Nx workspace itself and must integrate with Nx's project graph.

## Files to Create/Modify

- `packages/nx-boundary-plugin/src/index.ts` (new) — Plugin entry point exporting generators, executors, and project graph processor
- `packages/nx-boundary-plugin/src/generators/init/generator.ts` (new) — Generator that initializes boundary rules configuration in `nx.json` and tags projects based on their directory path
- `packages/nx-boundary-plugin/src/generators/init/schema.json` (new) — Generator schema defining input parameters
- `packages/nx-boundary-plugin/src/executors/boundary-lint/executor.ts` (new) — Custom executor that checks import statements against boundary rules
- `packages/nx-boundary-plugin/src/executors/boundary-lint/schema.json` (new) — Executor schema defining configuration options
- `packages/nx-boundary-plugin/src/rules/boundary-rules.ts` (new) — Boundary rule engine that evaluates import paths against allowed dependency patterns
- `packages/nx-boundary-plugin/src/utils/tag-resolver.ts` (new) — Utility that resolves project tags from directory structure (e.g., `libs/shared/ui` → tags: `["scope:shared", "type:ui"]`)
- `packages/nx-boundary-plugin/package.json` (new) — Package configuration with Nx plugin metadata
- `packages/nx-boundary-plugin/src/rules/boundary-rules.spec.ts` (new) — Unit tests for the boundary rule engine
- `packages/nx-boundary-plugin/src/utils/tag-resolver.spec.ts` (new) — Unit tests for the tag resolver

## Requirements

### Tag Resolution

- Projects under `libs/shared/` receive tags `["scope:shared", "type:{folder_name}"]` (e.g., `libs/shared/ui` → `["scope:shared", "type:ui"]`)
- Projects under `libs/feature/` receive tags `["scope:feature", "type:{folder_name}"]`
- Projects under `apps/` receive tags `["scope:app", "type:app"]`
- Projects not matching any pattern receive tag `["scope:unknown"]`
- Tag resolution must handle nested structures: `libs/shared/data-access/users` → `["scope:shared", "type:data-access"]` (uses first subdirectory after the category)

### Boundary Rules

- Rules are defined as a list of `{ "sourceTag": "<glob>", "onlyDependOnProjectsWithTags": ["<tag>", ...], "notDependOnProjectsWithTags": ["<tag>", ...] }`
- Rule evaluation: a project with tag matching `sourceTag` may only import from projects whose tags satisfy ALL of `onlyDependOnProjectsWithTags` and NONE of `notDependOnProjectsWithTags`
- Default rules (initialized by the generator):
  - `scope:shared` may not depend on `scope:feature` or `scope:app`
  - `scope:feature` may depend on `scope:shared` but not on other `scope:feature` projects
  - `scope:app` may depend on any scope
- Glob matching: `sourceTag` supports `*` wildcards (e.g., `scope:*` matches any scope tag)

### Boundary Lint Executor

- The executor reads boundary rules from `nx.json` under the key `boundaryRules`
- For each source file in the target project, it scans TypeScript import statements and resolves them to workspace project names via Nx's project graph
- Violations are reported as: `{ "file": "<path>", "line": <number>, "importedProject": "<name>", "sourceTag": "<tag>", "violatedRule": "<rule_description>" }`
- Exit code 0 if no violations; exit code 1 if any violations found
- The executor supports an `--affected` flag that limits checking to files changed since `main` branch (uses Nx's affected logic)

### Init Generator

- Running `nx generate @nx-boundary-plugin:init` adds the default boundary rules to `nx.json`
- The generator scans all projects and assigns tags based on directory structure using the tag resolver
- Tags are written to each project's `project.json` under the `tags` array
- If a project already has tags, the generator merges new tags without removing existing ones

### Expected Functionality

- Tag resolver for `libs/shared/ui` returns `["scope:shared", "type:ui"]`
- Tag resolver for `apps/web` returns `["scope:app", "type:app"]`
- Tag resolver for `tools/scripts` returns `["scope:unknown"]`
- A `scope:shared` project importing from a `scope:feature` project → violation reported with the correct rule reference
- A `scope:feature` project importing from a `scope:shared` project → no violation
- A `scope:app` project importing from any project → no violation
- Running the boundary-lint executor on a clean project → exit code 0
- Running the boundary-lint executor on a project with a forbidden import → exit code 1, violation details printed
- Running the init generator on a workspace with 5 projects → all 5 projects receive appropriate tags in their `project.json`

## Acceptance Criteria

- The tag resolver correctly derives scope and type tags from project directory paths for all specified patterns
- Boundary rules correctly evaluate allowed and forbidden cross-project dependencies using tag matching with glob support
- The boundary-lint executor scans TypeScript imports, resolves them to project names, and reports violations with file path, line number, and rule reference
- The init generator writes default boundary rules to `nx.json` and assigns tags to all workspace projects
- Existing project tags are preserved during init (merged, not overwritten)
- `pnpm install && pnpm build` succeeds with the plugin package included
- Unit tests cover tag resolution for all directory patterns, boundary rule evaluation for allowed/denied/wildcard cases, and edge cases (unknown scope, nested paths)
