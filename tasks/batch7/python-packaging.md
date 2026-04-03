# Task: Add PEP 735 Dependency Group Parsing to the packaging Library

## Background

The `packaging` library (https://github.com/pypa/packaging) provides utilities for working with Python packaging standards — version parsing, requirement specifiers, markers, and metadata. PEP 735 introduces "Dependency Groups" in `pyproject.toml` for declaring named groups of development/test/CI dependencies that are not part of the published package metadata. The task is to implement parsing, validation, and resolution of dependency groups within the existing packaging library infrastructure.

## Files to Create/Modify

- `packaging/dependency_groups.py` (create) — `DependencyGroup` and `DependencyGroupResolver` classes for parsing and resolving dependency groups from `pyproject.toml` data
- `packaging/requirements.py` (modify) — Add a `from_dependency_group_item` class method to the `Requirement` class for constructing requirements from dependency group entries
- `tests/test_dependency_groups.py` (create) — Unit tests covering parsing, validation, cross-group references, and error handling

## Requirements

### Dependency Group Data Format

Per PEP 735, `[dependency-groups]` in `pyproject.toml` defines named groups:

```toml
[dependency-groups]
test = ["pytest>=7.0", "coverage[toml]"]
lint = ["ruff>=0.1.0", "mypy>=1.0"]
dev = [{include-group = "test"}, {include-group = "lint"}, "pre-commit"]
docs = ["sphinx>=7.0", "sphinx-rtd-theme"]
```

Each group is a list of either:
- A string: a PEP 508 dependency specifier (same format as `Requirement`)
- A dict with `{include-group: "<group-name>"}`: references another dependency group

### `DependencyGroup` Class (`dependency_groups.py`)

```python
class DependencyGroup:
    def __init__(self, name: str, items: list[str | dict]):
```

#### Properties
- `name` — Group name string
- `requirements` — List of `Requirement` objects (only the direct string entries, not include-group references)
- `include_groups` — List of referenced group names (from `{include-group: ...}` entries)
- `raw_items` — The original items list as provided

#### Validation
- Each string item must be a valid PEP 508 requirement specifier (parseable by `Requirement`)
- Each dict item must have exactly one key `"include-group"` with a string value
- Invalid entries raise `InvalidDependencyGroup` with the group name and item index
- Group name must match `^[a-z0-9]([a-z0-9-]*[a-z0-9])?$` (lowercase alphanumeric with hyphens)

### `DependencyGroupResolver` Class (`dependency_groups.py`)

```python
class DependencyGroupResolver:
    def __init__(self, groups: dict[str, list]):
```

- `groups` — The full `[dependency-groups]` table from `pyproject.toml` (dict of group name → items list)

#### Methods

- `resolve(group_name: str) -> list[Requirement]`:
  1. Look up the group by name; raise `UndefinedDependencyGroup(group_name)` if not found
  2. Parse all string items as `Requirement` objects
  3. For each `{include-group: name}` entry, recursively resolve the referenced group
  4. Detect circular references: if resolving group A encounters group A again in the chain, raise `CircularDependencyGroup` with the cycle path (e.g., `["dev", "test", "dev"]`)
  5. Deduplicate requirements by package name (case-insensitive): if the same package appears multiple times (from different groups), keep the most constrained specifier (the one with the most version constraints)
  6. Return the flattened, deduplicated list of `Requirement` objects

- `resolve_all() -> dict[str, list[Requirement]]`:
  - Resolve all groups and return a dict mapping group name → resolved requirements

- `validate() -> list[str]`:
  - Return a list of validation error messages (empty if all groups are valid)
  - Check: all include-group references point to defined groups
  - Check: no circular dependencies exist
  - Check: all string items are valid PEP 508 specifiers

### `Requirement.from_dependency_group_item` Class Method

```python
@classmethod
def from_dependency_group_item(cls, item: str | dict) -> Requirement | None:
```
- If `item` is a string, parse and return a `Requirement`
- If `item` is a dict with `include-group`, return `None` (it's a reference, not a requirement)
- If `item` is any other type or dict format, raise `InvalidRequirement`

### Exception Classes

- `InvalidDependencyGroup(Exception)` — Raised for malformed group definitions; attributes: `group_name`, `item_index`, `message`
- `UndefinedDependencyGroup(Exception)` — Raised when referencing a non-existent group; attributes: `group_name`
- `CircularDependencyGroup(Exception)` — Raised on circular include-group references; attributes: `cycle` (list of group names forming the cycle)

## Expected Functionality

Given:
```python
groups = {
    "test": ["pytest>=7.0", "coverage[toml]"],
    "lint": ["ruff>=0.1.0", "mypy>=1.0"],
    "dev": [{"include-group": "test"}, {"include-group": "lint"}, "pre-commit"],
    "docs": ["sphinx>=7.0", "sphinx-rtd-theme"],
}
resolver = DependencyGroupResolver(groups)
```

- `resolver.resolve("test")` returns `[Requirement("pytest>=7.0"), Requirement("coverage[toml]")]`
- `resolver.resolve("dev")` returns `[Requirement("pytest>=7.0"), Requirement("coverage[toml]"), Requirement("ruff>=0.1.0"), Requirement("mypy>=1.0"), Requirement("pre-commit")]`
- `resolver.resolve("nonexistent")` raises `UndefinedDependencyGroup`
- Adding `{"include-group": "dev"}` to the "test" group creates a circular dependency: `resolver.resolve("test")` raises `CircularDependencyGroup(cycle=["test", "dev", "test"])`
- `resolver.validate()` returns `[]` for valid groups

## Acceptance Criteria

- `DependencyGroup` correctly parses string items as `Requirement` objects and dict items as include-group references
- Group name validation rejects invalid names (uppercase, special characters, leading/trailing hyphens)
- `DependencyGroupResolver.resolve` flattens include-group references recursively
- Circular dependencies are detected and raise `CircularDependencyGroup` with the correct cycle path
- Duplicate package names are deduplicated (case-insensitive)
- `validate()` reports all errors (undefined references, circular deps, invalid specifiers) without raising
- `Requirement.from_dependency_group_item` correctly handles both string and dict formats
- All exception classes have the specified attributes
- All tests pass including edge cases: empty groups, deeply nested include chains, groups with only include-group entries
