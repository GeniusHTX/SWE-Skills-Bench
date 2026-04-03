# Task: Implement a GitOps Manifest Reconciler for Flux CD

## Background

Flux CD (https://github.com/fluxcd/flux2) is a GitOps toolkit for Kubernetes. The project needs a Python-based manifest reconciliation engine that simulates Flux's core behavior: reading desired state from a Git repository structure, comparing it against current cluster state, computing diffs, and generating reconciliation plans. This engine is used for testing and validating GitOps configurations before applying them to a real cluster.

## Files to Create/Modify

- `tests/python/reconciler.py` (create) — `ManifestReconciler` class that loads Kubernetes manifests from a directory tree, compares desired vs current state, and produces a reconciliation plan with create/update/delete actions
- `tests/python/manifest_loader.py` (create) — `ManifestLoader` class that reads YAML files from a directory structure, parses multi-document YAML, validates required Kubernetes fields, and organizes manifests by kind/namespace/name
- `tests/python/diff_engine.py` (create) — `DiffEngine` class that computes structured diffs between two manifest versions, ignoring server-managed fields (status, metadata.resourceVersion, metadata.uid, metadata.creationTimestamp)
- `tests/python/sync_policy.py` (create) — `SyncPolicy` class implementing sync strategies: `apply` (create and update only), `prune` (delete resources not in Git), and `force` (recreate changed resources); with namespace filtering and resource exclusion rules
- `tests/test_gitops_workflow.py` (create) — Tests for manifest loading, diff computation, reconciliation planning, and sync policy enforcement

## Requirements

### ManifestLoader

- `load_directory(path: str) -> dict[str, dict]` — Recursively read all `.yaml` and `.yml` files from the path, parse each (supporting `---` multi-document separators), and return a dict keyed by `"{kind}/{namespace}/{name}"` (or `"{kind}/_cluster_/{name}"` for cluster-scoped resources)
- Required fields for each manifest: `apiVersion`, `kind`, `metadata.name`; if `metadata.namespace` is absent, classify as cluster-scoped
- `validate_manifest(manifest: dict) -> list[str]` — Return validation errors:
  - Missing `apiVersion`: `"Missing apiVersion"`
  - Missing `kind`: `"Missing kind"`
  - Missing `metadata.name`: `"Missing metadata.name"`
  - Labels not a flat string-to-string dict: `"Labels must be string key-value pairs"`
- Skip files that fail validation and log a warning (store in `loader.warnings: list[str]`)
- Handle empty YAML documents (null after parsing) gracefully by skipping them

### DiffEngine

- `diff(desired: dict, current: dict) -> dict`:
  - Compare field by field, ignoring keys in `IGNORED_FIELDS = {"status", "metadata.resourceVersion", "metadata.uid", "metadata.creationTimestamp", "metadata.generation", "metadata.managedFields"}`
  - Return `{"added": dict, "removed": dict, "changed": dict}` where `changed` maps field paths to `{"old": value, "new": value}`
  - Nested dict comparison: use dot-notation paths (e.g., `"spec.replicas"`, `"spec.template.spec.containers[0].image"`)
  - Array comparison: compare element by element by index; if arrays differ in length, include the length change
- `has_changes(desired: dict, current: dict) -> bool` — Return True if `diff()` would produce any non-empty section
- `format_diff(diff_result: dict) -> str` — Human-readable diff output with `+` for additions, `-` for removals, `~` for changes

### ManifestReconciler

- Constructor: `ManifestReconciler(desired_manifests: dict[str, dict], current_manifests: dict[str, dict], sync_policy: SyncPolicy)`
- `reconcile() -> list[dict]` — Produce a reconciliation plan as a list of actions:
  - `{"action": "create", "resource_key": str, "manifest": dict}` for resources in desired but not in current
  - `{"action": "update", "resource_key": str, "manifest": dict, "diff": dict}` for resources in both but with changes
  - `{"action": "delete", "resource_key": str, "manifest": dict}` for resources in current but not in desired (only if sync policy has `prune=True`)
  - `{"action": "skip", "resource_key": str, "reason": str}` for excluded resources
  - `{"action": "unchanged", "resource_key": str}` for identical resources
- Actions must be ordered: creates first, then updates, then deletes
- Apply namespace filtering: only reconcile resources in namespaces allowed by the sync policy

### SyncPolicy

- Constructor: `SyncPolicy(prune: bool = False, force: bool = False, namespaces: list[str] = None, excluded_kinds: list[str] = None)`
- `prune`: If True, generate delete actions for orphaned resources
- `force`: If True, change update actions to `"recreate"` (delete + create)
- `namespaces`: If set, only reconcile resources in these namespaces; cluster-scoped resources always included
- `excluded_kinds`: List of Kubernetes kinds to skip (e.g., `["Secret", "CustomResourceDefinition"]`)
- `should_include(resource_key: str, manifest: dict) -> bool` — Return whether a resource should be reconciled based on namespace and kind filters
- `get_action_type(has_changes: bool, exists_in_current: bool, exists_in_desired: bool) -> str` — Determine the action type based on policy

### Edge Cases

- YAML file with syntax errors: skip the file, add to `warnings`
- Manifest with no `metadata` key at all: validation catches it with `"Missing metadata.name"`
- Desired and current manifests both empty: reconcile returns empty list
- Resource in excluded_kinds that also has changes: action is `"skip"` with reason `"Excluded kind: {kind}"`
- Multi-document YAML where one document is valid and another is invalid: include the valid document, skip the invalid one

## Expected Functionality

- Loading a directory with 3 YAML files containing 5 manifests (2 Deployments, 2 Services, 1 ConfigMap) produces a dict of 5 entries keyed by kind/namespace/name
- Diffing a Deployment where `spec.replicas` changed from 2 to 3 produces `{"changed": {"spec.replicas": {"old": 2, "new": 3}}}`
- Reconciling 5 desired manifests against 4 current (1 new, 1 changed, 1 deleted, 2 unchanged) with `prune=True` produces 1 create + 1 update + 1 delete + 2 unchanged actions
- With `excluded_kinds=["Secret"]`, Secret resources are skipped regardless of changes

## Acceptance Criteria

- `ManifestLoader` correctly parses multi-document YAML files and organizes manifests by kind/namespace/name
- Invalid manifests are skipped with warnings, not exceptions
- `DiffEngine` produces accurate field-level diffs ignoring server-managed fields
- `ManifestReconciler` generates correct reconciliation plans with proper action ordering
- `SyncPolicy` enforces prune, force, namespace, and kind-based filtering
- Edge cases (empty dirs, malformed YAML, empty documents) are handled gracefully
- All tests pass with `pytest`
