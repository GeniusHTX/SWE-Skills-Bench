# Task: Implement Project Dependency Graph Analyzer with Module Boundary Enforcement for Nx Workspace

## Background

The Nx monorepo toolkit (`nrwl/nx`) needs a project dependency graph analyzer within the `packages/` directory that reads `project.json` configurations, builds an in-memory dependency graph, enforces module boundary constraints based on project tags, and computes affected projects from a set of changed files. The analyzer must support the standard Nx library taxonomy (feature, ui, data-access, util) and scope-based access rules, and expose a caching layer that tracks project input hashes.

## Files to Create/Modify

- `packages/nx/src/graph/dependency-analyzer.ts` — Dependency graph builder and analyzer (new)
- `packages/nx/src/graph/dependency-analyzer.spec.ts` — Unit tests for the dependency analyzer (new)
- `packages/nx/src/graph/boundary-enforcer.ts` — Module boundary constraint checker based on project tags (new)
- `packages/nx/src/graph/boundary-enforcer.spec.ts` — Unit tests for boundary enforcement (new)
- `packages/nx/src/graph/affected-calculator.ts` — Computes affected projects from changed file paths (new)
- `packages/nx/src/graph/affected-calculator.spec.ts` — Unit tests for affected calculation (new)
- `packages/nx/src/graph/cache-manager.ts` — Task caching manager with hash computation and invalidation (new)
- `packages/nx/src/graph/cache-manager.spec.ts` — Unit tests for cache management (new)

## Requirements

### Dependency Graph Builder

- `DependencyAnalyzer` class accepts an array of `ProjectConfiguration` objects, each with: `name: string`, `root: string`, `sourceRoot: string`, `projectType: 'application' | 'library'`, `tags: string[]`, `targets: Record<string, TargetConfiguration>`, `implicitDependencies: string[]`
- `buildGraph()` returns a `ProjectGraph` with `nodes: Record<string, ProjectGraphNode>` and `dependencies: Record<string, ProjectGraphDependency[]>`
- Dependencies are inferred from: `implicitDependencies` array, and import scanning (accept a `resolveImports: (filePath: string) => string[]` callback)
- Detect circular dependencies and return them as `CircularDependencyError` with the full cycle path (e.g., `A → B → C → A`)
- `getTopologicalOrder()` returns project names in a valid build order; throws if cycles exist

### Module Boundary Enforcer

- `BoundaryEnforcer` accepts an array of `DepConstraint` rules: `{ sourceTag: string, onlyDependOnLibsWithTags: string[] }`
- `enforce(graph: ProjectGraph)` returns an array of `BoundaryViolation` objects: `{ source: string, target: string, sourceTag: string, allowedTags: string[], actualTargetTags: string[] }`
- Rules to enforce:
  - `type:app` can depend on `type:feature`, `type:ui`, `type:data-access`, `type:util`
  - `type:feature` can depend on `type:ui`, `type:data-access`, `type:util`
  - `type:ui` can depend on `type:ui`, `type:util`
  - `type:data-access` can depend on `type:data-access`, `type:util`
  - `type:util` can depend on `type:util` only
  - Scope constraints: `scope:web` can depend on `scope:web` and `scope:shared`; `scope:api` on `scope:api` and `scope:shared`; `scope:shared` on `scope:shared` only
- A project with no tags is unrestricted (no violations generated for it as a source)
- A dependency target with no matching tags for the constraint generates a violation

### Affected Calculator

- `AffectedCalculator` accepts a `ProjectGraph` and a mapping of `projectRoot → projectName`
- `getAffectedProjects(changedFiles: string[])` returns the set of directly and transitively affected project names
- A file `libs/shared/ui/src/button.ts` maps to project `shared-ui` via its `sourceRoot`
- All projects that depend (directly or transitively) on `shared-ui` are included in the affected set
- Files outside any project root return an empty affected set (no error)
- If the root `nx.json` or `package.json` is changed, all projects are affected

### Cache Manager

- `CacheManager` class with `computeHash(projectName: string, target: string, inputs: string[])` that returns a SHA-256 hex digest of the concatenated inputs
- `store(hash: string, output: CacheEntry)` and `retrieve(hash: string): CacheEntry | undefined` — `CacheEntry` contains `outputPaths: string[]`, `timestamp: number`, `duration: number`
- `isValid(hash: string, currentInputs: string[])` returns `true` only if stored hash matches `computeHash` of current inputs
- `invalidate(projectName: string)` removes all cache entries for a project
- `getStats()` returns `{ hits: number, misses: number, totalEntries: number }`

### Expected Functionality

- Graph with `web (app)` → `feature-auth (feature)` → `shared-ui (ui)` → `util-format (util)` → `buildGraph()` produces correct dependency edges
- Graph with `A → B → A` → `buildGraph()` throws `CircularDependencyError` with cycle `["A", "B", "A"]`
- `getTopologicalOrder()` on `web → auth → ui → util` returns `["util", "ui", "auth", "web"]` (or valid topological alternative)
- Boundary enforcer: `feature-auth` (tags: `type:feature, scope:web`) depends on `shared-ui` (tags: `type:ui, scope:shared`) → no violation
- Boundary enforcer: `util-format` (tags: `type:util`) depends on `feature-auth` (tags: `type:feature`) → violation: `type:util` cannot depend on `type:feature`
- Boundary enforcer: `scope:web` project depends on `scope:api` project → violation for scope constraint
- Affected: changed file `libs/shared/ui/src/button.ts` → affected set includes `shared-ui`, `feature-auth`, `web`
- Affected: changed file `nx.json` → all projects affected
- Affected: changed file `README.md` (outside all projects) → empty affected set
- Cache: `computeHash("web", "build", ["hash1", "hash2"])` → deterministic hex string; same inputs always produce same hash
- Cache: store then retrieve with same hash → returns entry; retrieve with different hash → returns undefined

## Acceptance Criteria

- `pnpm jest packages/nx/src/graph/dependency-analyzer.spec.ts` passes all tests
- `pnpm jest packages/nx/src/graph/boundary-enforcer.spec.ts` passes all tests
- `pnpm jest packages/nx/src/graph/affected-calculator.spec.ts` passes all tests
- `pnpm jest packages/nx/src/graph/cache-manager.spec.ts` passes all tests
- Circular dependency detection reports the full cycle path
- Topological ordering is valid (every dependency appears before its dependent)
- Module boundary enforcement catches type-level and scope-level violations independently
- Affected calculation includes transitive dependents, not just direct dependents
- Global config file changes mark all projects as affected
- Cache hash computation is deterministic and uses SHA-256
- Cache invalidation removes all entries for the specified project
- No hardcoded project names in test assertions — tests construct their own graph fixtures
