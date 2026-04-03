# Task: Implement a Project Constraint Enforcement Plugin for Nx

## Background

Nx (https://github.com/nrwl/nx) is a build system and monorepo tool. Project boundaries in Nx enforce dependency rules between libraries, but the built-in tag-based constraint system is limited. The task is to implement a custom Nx plugin that enforces fine-grained project constraints: layer-based dependency rules, circular dependency detection, public API boundary enforcement, and maximum dependency depth limits.

## Files to Create/Modify

- `packages/nx/src/plugins/project-constraints/index.ts` (create) — Plugin entry point that registers the constraint enforcement rules
- `packages/nx/src/plugins/project-constraints/constraint-checker.ts` (create) — `ConstraintChecker` class that validates project dependencies against configured rules
- `packages/nx/src/plugins/project-constraints/rules/layer-rule.ts` (create) — Layer-based dependency rule (e.g., `ui` cannot import `data-access` directly)
- `packages/nx/src/plugins/project-constraints/rules/circular-rule.ts` (create) — Circular dependency detection rule
- `packages/nx/src/plugins/project-constraints/rules/public-api-rule.ts` (create) — Public API boundary enforcement rule
- `packages/nx/src/plugins/project-constraints/rules/depth-rule.ts` (create) — Maximum transitive dependency depth rule
- `packages/nx/src/plugins/project-constraints/__tests__/constraint-checker.spec.ts` (create) — Unit tests for the constraint checker
- `packages/nx/src/plugins/project-constraints/__tests__/rules.spec.ts` (create) — Unit tests for individual rules

## Requirements

### Configuration Schema

The plugin reads its configuration from `nx.json` under the key `projectConstraints`:

```json
{
  "projectConstraints": {
    "layers": {
      "order": ["ui", "feature", "data-access", "util"],
      "allowSameLayer": true,
      "allowSkipLayers": false
    },
    "maxDepth": 5,
    "publicApiPattern": "src/index.ts",
    "customRules": [
      {
        "sourceTag": "scope:client",
        "notDependOnTags": ["scope:server", "scope:admin"],
        "allowDependOnTags": ["scope:shared"]
      }
    ]
  }
}
```

### `ConstraintChecker` Class (`constraint-checker.ts`)

```typescript
interface ConstraintViolation {
  rule: string;           // "layer", "circular", "public-api", "depth", "custom"
  severity: "error" | "warning";
  sourceProject: string;
  targetProject?: string;
  message: string;
  filePath?: string;
  line?: number;
}

class ConstraintChecker {
  constructor(
    projectGraph: ProjectGraph,
    config: ProjectConstraintsConfig
  );

  checkAll(): ConstraintViolation[];
  checkProject(projectName: string): ConstraintViolation[];
  checkDependency(source: string, target: string): ConstraintViolation[];
}
```

- `projectGraph` is the Nx `ProjectGraph` containing all projects and their dependencies
- `checkAll()` runs all configured rules against all projects and returns combined violations
- `checkProject(name)` checks only dependencies of the specified project
- `checkDependency(source, target)` checks a single dependency edge

### Layer Rule (`layer-rule.ts`)

```typescript
function checkLayerRule(
  source: ProjectGraphProjectNode,
  target: ProjectGraphProjectNode,
  config: LayerConfig
): ConstraintViolation | null;
```

- Each project's layer is determined by its tags (e.g., tag `type:ui` → layer `ui`)
- The `order` array defines the layer hierarchy from top to bottom
- A project in layer `i` can only depend on projects in layer `i+1` or below
- If `allowSameLayer` is true, projects in the same layer can depend on each other
- If `allowSkipLayers` is false, a `ui` project cannot depend directly on `util` — it must go through `feature` or `data-access`
- Return a `ConstraintViolation` with `rule: "layer"` if the dependency violates the layer order

### Circular Dependency Rule (`circular-rule.ts`)

```typescript
function detectCircularDependencies(
  projectGraph: ProjectGraph
): ConstraintViolation[];
```

- Perform a depth-first search on the project dependency graph
- Detect all cycles and return a `ConstraintViolation` for each unique cycle found
- The violation message includes the full cycle path: `"Circular dependency: A → B → C → A"`
- Each unique cycle is reported once (not once per node in the cycle)
- Self-dependencies (A → A) are also reported

### Public API Rule (`public-api-rule.ts`)

```typescript
function checkPublicApiRule(
  source: ProjectGraphProjectNode,
  target: ProjectGraphProjectNode,
  dependency: ProjectGraphDependency,
  publicApiPattern: string
): ConstraintViolation | null;
```

- A project's public API is defined by its entry point file matching `publicApiPattern` (default: `src/index.ts`)
- If project A imports from project B via a path that does NOT go through B's public API entry point (e.g., importing `@myorg/lib-b/src/internal/helper` instead of `@myorg/lib-b`), return a violation
- The check examines the `dependency.source` file import path
- Return `null` if the import goes through the public API

### Depth Rule (`depth-rule.ts`)

```typescript
function checkDepthRule(
  projectName: string,
  projectGraph: ProjectGraph,
  maxDepth: number
): ConstraintViolation | null;
```

- Compute the maximum transitive dependency depth for the given project using BFS
- Depth is the longest chain: if A → B → C → D, then A has depth 3
- If the depth exceeds `maxDepth`, return a `ConstraintViolation` with the actual depth and the longest chain
- The violation message includes the chain: `"Project 'app' has dependency depth 6 (max: 5): app → feat-a → data-a → util-a → util-b → util-c → util-d"`

### Plugin Entry Point (`index.ts`)

```typescript
export const createNodes: CreateNodes = [
  '**/project.json',
  (configFilePath, options, context) => {
    // Register constraint checker
  }
];
```

- Register the plugin so it runs during `nx lint` or a custom `nx check-constraints` target
- Load configuration from `nx.json`
- Run `ConstraintChecker.checkAll()` and report violations
- Exit with error code 1 if any violations have severity `"error"`

## Expected Functionality

- Given projects tagged `type:ui`, `type:feature`, `type:data-access`, `type:util` with layer order `[ui, feature, data-access, util]`:
  - A `ui` project depending on a `feature` project: allowed
  - A `data-access` project depending on a `ui` project: violation (lower layer depending on upper layer)
  - With `allowSkipLayers: false`, a `ui` project depending directly on `util`: violation

- Given a graph A → B → C → A: one circular dependency violation with cycle path `["A", "B", "C", "A"]`

- Given a project importing `@myorg/lib-b/src/internal/helper.ts` instead of `@myorg/lib-b`: public API violation

- Given a dependency chain of depth 6 with `maxDepth: 5`: depth violation with the full chain

## Acceptance Criteria

- Layer rule correctly enforces directional dependencies based on configured layer order
- `allowSameLayer` and `allowSkipLayers` options are respected
- Circular dependency detection finds all unique cycles using DFS
- Public API rule detects deep imports that bypass the project's entry point
- Depth rule computes correct transitive dependency depth using BFS
- `ConstraintChecker.checkAll()` aggregates violations from all rules
- `ConstraintChecker.checkProject()` checks only the specified project's dependencies
- The plugin builds without errors as part of the Nx package
- All unit tests pass with mock project graphs covering valid and invalid dependency patterns
