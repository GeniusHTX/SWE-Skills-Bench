# Task: Implement PEP 621 Metadata Validator and Build Backend Shim for the Packaging Library

## Background

The Python `packaging` library (`pypa/packaging`) provides low-level utilities for version parsing, specifiers, and markers but lacks tooling to validate `pyproject.toml` metadata against PEP 621, inspect `[build-system]` tables, and resolve optional-dependency groups. A new `packaging/metadata/` subpackage is needed that parses `pyproject.toml` files, validates all PEP 621 fields, detects common misconfiguration errors, and provides a build-backend resolution utility that identifies which build backend (setuptools, hatchling, flit, poetry) is configured and verifies that `requires` lists are satisfiable.

## Files to Create/Modify

- `packaging/metadata/__init__.py` (new) — Subpackage init, re-export `PyProjectValidator`, `BuildSystemInfo`, `DependencyResolver`
- `packaging/metadata/validator.py` (new) — `PyProjectValidator` class that loads a `pyproject.toml` file, validates `[project]` table fields per PEP 621 (name, version, description, requires-python, dependencies, optional-dependencies, scripts, entry-points, classifiers, urls), and returns structured validation results
- `packaging/metadata/build_system.py` (new) — `BuildSystemInfo` class that parses the `[build-system]` table, identifies the build backend name, validates that `build-backend` is a dotted path string, checks that `requires` entries are valid PEP 508 dependency specifiers, and detects conflicts between backend name and requires list
- `packaging/metadata/dependency_resolver.py` (new) — `DependencyResolver` class that takes parsed `[project.dependencies]` and `[project.optional-dependencies]`, validates each entry as PEP 508, detects self-referencing optional groups (e.g., `all = ["my-package[dev,docs]"]`), detects circular optional-dependency references, and normalizes package names per PEP 503
- `tests/test_pyproject_validator.py` (new) — Unit tests for PEP 621 validation covering valid minimal configs, full-featured configs, and error cases
- `tests/test_build_system.py` (new) — Unit tests for build-system parsing and backend identification
- `tests/test_dependency_resolver.py` (new) — Unit tests for dependency validation, self-reference detection, and name normalization

## Requirements

### PyProjectValidator (`validator.py`)

- `__init__(self, toml_content: str)` — parse the TOML string; raise `ValueError` if TOML is syntactically invalid
- Method `validate() -> ValidationResult` returning an object with `is_valid: bool`, `errors: list[str]`, `warnings: list[str]`
- Required field checks:
  - `[project].name` must exist, be a string, contain only ASCII alphanumerics, hyphens, underscores, and dots, and not start/end with a hyphen or dot
  - `[project].version` must exist (or be listed in `dynamic`), and if present must be a valid version per PEP 440 (use `packaging.version.Version` to parse)
  - `[project].requires-python` if present must be a valid specifier set (use `packaging.specifiers.SpecifierSet`)
- Optional field validation:
  - `[project].dependencies` — each entry must be a valid PEP 508 requirement string (use `packaging.requirements.Requirement`)
  - `[project].optional-dependencies` — each group value must be a list of valid PEP 508 strings
  - `[project].classifiers` — each must be a string; warn if it doesn't match the `"Topic :: Subtopic"` pattern
  - `[project].scripts` and `[project.entry-points]` — values must be `"module:attribute"` dotted path strings
  - `[project].urls` — values must be strings starting with `http://` or `https://`
- Warning cases (not errors): missing `description`, missing `readme`, missing `license`, classifiers with unknown top-level categories
- Error: `version` not in `[project]` and not in `dynamic` list → error "version must be specified or listed in dynamic"
- Error: `name` missing → error "project name is required"

### BuildSystemInfo (`build_system.py`)

- `__init__(self, toml_content: str)` — parse TOML and extract `[build-system]` table; raise `ValueError` if `[build-system]` table is missing
- Property `backend_name -> str` — return the `build-backend` value (e.g., `"setuptools.build_meta"`)
- Property `backend_type -> str` — return one of `"setuptools"`, `"hatchling"`, `"flit"`, `"poetry"`, `"pdm"`, `"unknown"` based on matching the `build-backend` string
- Property `requires -> list[str]` — return the `requires` list
- Method `validate() -> ValidationResult` with checks:
  - `build-backend` must be a non-empty string containing at least one dot (module path)
  - Each entry in `requires` must be a valid PEP 508 requirement
  - If `backend_type` is `"setuptools"`, `requires` should include a package matching `"setuptools"` — warn if not
  - If `backend_type` is `"hatchling"`, `requires` should include `"hatchling"` — warn if not
- Method `is_pep517_compliant() -> bool` — return `True` if both `build-backend` and `requires` are present

### DependencyResolver (`dependency_resolver.py`)

- `__init__(self, dependencies: list[str], optional_dependencies: dict[str, list[str]], project_name: str)`
- Method `validate_all() -> ValidationResult` — validate all dependency and optional-dependency strings as PEP 508
- Method `detect_self_references() -> list[str]` — return group names that contain a dependency on `project_name` itself (normalized), e.g., `all = ["my-package[dev]"]` when `project_name = "my-package"`
- Method `detect_circular_extras() -> list[tuple[str, str]]` — detect cycles in optional-dependency references, e.g., group `a` references `my-package[b]` and group `b` references `my-package[a]` → return `[("a", "b")]`
- Method `normalize_name(name: str) -> str` — per PEP 503, lowercase and replace runs of `[-_.]` with a single `-`
- Method `get_all_extras() -> list[str]` — return sorted list of optional-dependency group names
- Method `resolve_extras(group: str) -> list[str]` — return the flat, deduplicated list of concrete (non-self-referencing) dependencies required when installing `project_name[group]`, transitively expanding any self-referential extras

### Expected Functionality

- Minimal valid `pyproject.toml` with just `name` and `version` → `validate()` returns `is_valid=True`, no errors
- Missing `name` field → error list contains "project name is required"
- `version = "not.a.version"` → error about invalid PEP 440 version
- `requires-python = ">=3.8"` → valid; `requires-python = "python3"` → error about invalid specifier
- `dependencies = ["requests>=2.28.0"]` → valid; `dependencies = ["not a valid spec!!!"]` → error
- `scripts = {"my-cli": "my_package.cli:main"}` → valid; `scripts = {"bad": "no_colon"}` → error
- `urls = {"Homepage": "https://example.com"}` → valid; `urls = {"Homepage": "ftp://bad"}` → error
- Build system with `build-backend = "setuptools.build_meta"` and `requires = ["setuptools>=61.0"]` → `backend_type = "setuptools"`, `is_pep517_compliant() = True`
- Build system with `build-backend = "setuptools.build_meta"` and `requires = ["wheel"]` (no setuptools) → warning about missing setuptools in requires
- Build system missing `[build-system]` table entirely → raises `ValueError`
- Build system with `build-backend = ""` → error about empty backend string
- `normalize_name("My_Package.Name")` → `"my-package-name"`
- `normalize_name("my---package")` → `"my-package"`
- Optional deps `{"dev": ["pytest"], "all": ["my-package[dev]"]}` with `project_name="my-package"` → `detect_self_references()` returns `["all"]`
- `resolve_extras("all")` for the above → returns `["pytest"]`
- Circular extras: `{"a": ["pkg[b]"], "b": ["pkg[a]"]}` with `project_name="pkg"` → `detect_circular_extras()` returns `[("a", "b")]`

## Acceptance Criteria

- `python -m pytest tests/test_pyproject_validator.py -v` passes all tests
- `python -m pytest tests/test_build_system.py -v` passes all tests
- `python -m pytest tests/test_dependency_resolver.py -v` passes all tests
- Validator correctly accepts minimal PEP 621 pyproject.toml files and rejects those with missing required fields
- Version strings are validated against PEP 440 using `packaging.version.Version`
- Dependency strings are validated against PEP 508 using `packaging.requirements.Requirement`
- Build backend is correctly identified as setuptools, hatchling, flit, poetry, pdm, or unknown
- Self-referencing optional-dependency groups are detected and reported
- Circular extra references are detected even across multiple levels of indirection
- Package name normalization follows PEP 503 exactly
- No new dependencies beyond `tomli` (for Python < 3.11) and the `packaging` library itself
