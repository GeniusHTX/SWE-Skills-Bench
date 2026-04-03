# Task: Create a Distributable Python Package for the Packaging Library's Test Utilities

## Background

The Python Packaging Authority's `packaging` library (https://github.com/pypa/packaging) provides core utilities for version parsing, specifier matching, and requirements handling. The project's internal test helpers — version fixtures, marker evaluation utilities, and specifier test factories — are useful for downstream projects that build on `packaging` but are not currently exposed as an installable package. A new `packaging-test-utils` package needs to be created within the repository, following modern Python packaging standards (PEP 621, PEP 517/518) with proper metadata, entry points, and distribution configuration.

## Files to Create/Modify

- `packaging_test_utils/pyproject.toml` (create) — Package metadata following PEP 621 with build system specification (PEP 517/518), dependencies on `packaging`, optional test extras, and classifiers
- `packaging_test_utils/src/packaging_test_utils/__init__.py` (create) — Package init exposing public API: `VersionFactory`, `SpecifierFactory`, `MarkerEvaluator`
- `packaging_test_utils/src/packaging_test_utils/versions.py` (create) — `VersionFactory` class that generates `packaging.version.Version` objects from shorthand strings, supporting pre-release, post-release, dev, and local version segments
- `packaging_test_utils/src/packaging_test_utils/specifiers.py` (create) — `SpecifierFactory` class that generates `packaging.specifiers.SpecifierSet` objects with builder-pattern syntax and produces canonical string representations
- `packaging_test_utils/src/packaging_test_utils/markers.py` (create) — `MarkerEvaluator` class that evaluates `packaging.markers.Marker` expressions against custom environment dictionaries
- `packaging_test_utils/tests/test_versions.py` (create) — Tests for `VersionFactory` including edge cases (epochs, pre/post/dev combinations, local versions)
- `packaging_test_utils/tests/test_specifiers.py` (create) — Tests for `SpecifierFactory` including complex specifier sets and version matching
- `packaging_test_utils/tests/test_markers.py` (create) — Tests for `MarkerEvaluator` including boolean logic, platform markers, and undefined variables
- `packaging_test_utils/README.md` (create) — Package documentation with installation instructions, API overview, and usage examples

## Requirements

### pyproject.toml Configuration

- Build system must use `hatchling` as the build backend (`[build-system]` section with `requires = ["hatchling"]` and `build-backend = "hatchling.build"`)
- `[project]` section must include: `name = "packaging-test-utils"`, `version`, `description`, `requires-python = ">=3.9"`, `license = {text = "Apache-2.0"}`, `dependencies = ["packaging>=24.0"]`
- `[project.optional-dependencies]` must include `test = ["pytest>=8.0", "pytest-cov"]`
- Source layout must use the `src/` directory convention
- `[tool.hatch.build.targets.wheel]` must specify `packages = ["src/packaging_test_utils"]`
- Classifiers must include appropriate Python version, license, and topic classifiers

### VersionFactory

- `VersionFactory.create(version_str: str) -> Version` — parses a version string and returns a `packaging.version.Version`
- `VersionFactory.sequence(base: str, count: int) -> list[Version]` — generates a sequence of incrementing patch versions starting from `base` (e.g., `sequence("1.0.0", 3)` → `[1.0.0, 1.0.1, 1.0.2]`)
- `VersionFactory.pre_release_set(base: str) -> list[Version]` — generates `[{base}a1, {base}b1, {base}rc1, {base}]` for testing sort order
- Must reject invalid version strings by raising `packaging.version.InvalidVersion`

### SpecifierFactory

- `SpecifierFactory.from_spec(spec_str: str) -> SpecifierSet` — parses a specifier string
- `SpecifierFactory.range(min_version: str, max_version: str, include_min: bool = True, include_max: bool = False) -> SpecifierSet` — builds a range specifier (e.g., `range("1.0", "2.0")` → `>=1.0,<2.0`)
- `SpecifierFactory.compatible(version: str) -> SpecifierSet` — builds a compatible release specifier (e.g., `compatible("1.4")` → `~=1.4`)
- `SpecifierFactory.matches(specifier: SpecifierSet, versions: list[str]) -> list[Version]` — filters versions matching the specifier, returning sorted `Version` objects

### MarkerEvaluator

- `MarkerEvaluator.evaluate(marker_str: str, environment: dict | None = None) -> bool` — evaluates a PEP 508 marker against a custom environment dictionary; uses the current environment if `environment` is `None`
- `MarkerEvaluator.required_on(marker_str: str, platforms: list[str]) -> dict[str, bool]` — evaluates the marker against each named platform (providing standard environment values for `"linux"`, `"windows"`, `"macos"`) and returns a mapping of platform name to boolean
- Must handle complex markers with `and`, `or`, parentheses, and nested expressions
- Must raise `packaging.markers.InvalidMarker` for malformed marker strings

### Package Structure

- The package must use src-layout (`packaging_test_utils/src/packaging_test_utils/`)
- An editable install (`pip install -e ".[test]"`) must work correctly
- `python -m build` from the package directory must produce both wheel and sdist artifacts

## Expected Functionality

- `VersionFactory.create("1.2.3")` returns a `Version` object with `major=1, minor=2, micro=3`
- `VersionFactory.sequence("2.0.0", 3)` returns `[Version("2.0.0"), Version("2.0.1"), Version("2.0.2")]`
- `VersionFactory.pre_release_set("3.0")` returns versions sorted as `3.0a1 < 3.0b1 < 3.0rc1 < 3.0`
- `SpecifierFactory.range("1.0", "2.0")` creates `SpecifierSet(">=1.0,<2.0")` that matches `1.5.0` but not `2.0.0`
- `MarkerEvaluator.evaluate('sys_platform == "linux"', {"sys_platform": "linux"})` returns `True`
- `MarkerEvaluator.required_on('sys_platform == "win32"', ["linux", "windows", "macos"])` returns `{"linux": False, "windows": True, "macos": False}`
- `VersionFactory.create("not_a_version")` raises `InvalidVersion`

## Acceptance Criteria

- `pyproject.toml` follows PEP 621 with hatchling build backend, src-layout, correct dependencies, and optional test extras
- The package is installable with `pip install -e ".[test]"` and importable as `import packaging_test_utils`
- `VersionFactory` creates, sequences, and pre-release-set generates `packaging.version.Version` objects correctly, including edge cases (epochs, local versions, pre/post/dev)
- `SpecifierFactory` builds range and compatible-release specifiers that correctly filter version lists
- `MarkerEvaluator` evaluates PEP 508 markers against custom environments and predefined platform profiles
- Invalid inputs raise the appropriate `packaging` exceptions (`InvalidVersion`, `InvalidMarker`)
- All tests pass with `pytest` and achieve ≥ 80% coverage
