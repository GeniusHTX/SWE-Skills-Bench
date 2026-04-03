# Task: Create a Distributable CLI Tool Package for Python Version String Parsing

## Background

The packaging project (https://github.com/pypa/packaging) provides utilities for working with Python packaging standards. A new CLI tool package called `version-inspector` is needed that parses, compares, and analyzes Python version strings (PEP 440). The package must be properly structured for distribution to PyPI with modern packaging standards, entry points, and comprehensive metadata.

## Files to Create/Modify

- `src/version_inspector/__init__.py` (create) — Package initialization with `__version__` and public API exports
- `src/version_inspector/cli.py` (create) — Click-based CLI with subcommands: `parse`, `compare`, `check`, `range`
- `src/version_inspector/core.py` (create) — Core logic for version parsing, comparison, range checking, and pre-release detection
- `src/version_inspector/output.py` (create) — Output formatters for JSON and table display
- `pyproject.toml` (create) — Complete project configuration with build system, metadata, dependencies, optional dependencies, entry points, and classifiers
- `README.md` (create) — Package documentation with installation, usage examples, and API reference
- `tests/test_cli.py` (create) — CLI integration tests using Click's test runner
- `tests/test_core.py` (create) — Unit tests for core version parsing and comparison logic

## Requirements

### Package Structure

- Use the `src/` layout: all package code under `src/version_inspector/`.
- The `pyproject.toml` must use `setuptools` as the build backend.
- The package must declare:
  - `name = "version-inspector"`
  - `version` read dynamically from `src/version_inspector/__init__.py`
  - `requires-python = ">=3.9"`
  - Core dependencies: `click>=8.0`, `packaging>=23.0`
  - Optional dependency group `dev`: `pytest>=7.0`, `pytest-cov`, `click[testing]`
- A console script entry point `version-inspector` must point to `version_inspector.cli:main`.

### CLI Commands

- `version-inspector parse <version>`:
  - Parses a PEP 440 version string and outputs its components.
  - Output fields: `major`, `minor`, `micro`, `pre` (pre-release tag or null), `post` (post-release number or null), `dev` (dev number or null), `local` (local segment or null), `is_prerelease` (bool), `epoch`.
  - Example: `version-inspector parse 2.1.0rc1` → `{"major": 2, "minor": 1, "micro": 0, "pre": ["rc", 1], "is_prerelease": true, ...}`.
  - Invalid version strings must output an error message to stderr and exit with code 1.

- `version-inspector compare <version1> <version2>`:
  - Compares two version strings and outputs which is greater, or if they are equal.
  - Output: `{"version1": "...", "version2": "...", "result": "greater" | "less" | "equal"}`.
  - Must handle pre-release ordering: `1.0.0a1 < 1.0.0b1 < 1.0.0rc1 < 1.0.0`.

- `version-inspector check <version> --specifier <spec>`:
  - Checks whether a version satisfies a PEP 440 version specifier.
  - Example: `version-inspector check 2.1.0 --specifier ">=2.0,<3.0"` → `{"version": "2.1.0", "specifier": ">=2.0,<3.0", "satisfies": true}`.
  - Invalid specifiers must output an error message to stderr and exit with code 1.

- `version-inspector range <specifier> --versions <v1,v2,v3,...>`:
  - Filters a comma-separated list of versions against a specifier.
  - Returns the matching versions sorted in ascending order.
  - Example: `version-inspector range ">=1.5" --versions "1.0,1.5,2.0,1.3"` → `{"specifier": ">=1.5", "matching": ["1.5", "2.0"]}`.

- All commands must support a `--format` flag with values `json` (default) and `table`.

### Error Handling

- Invalid PEP 440 version strings → stderr: `Error: '{input}' is not a valid PEP 440 version`, exit code 1.
- Invalid specifier strings → stderr: `Error: '{input}' is not a valid PEP 440 specifier`, exit code 1.
- Missing required arguments → Click's built-in help/error message, exit code 2.

### Expected Functionality

- `version-inspector parse 1.0.0` → `{"major": 1, "minor": 0, "micro": 0, "pre": null, "post": null, "dev": null, "local": null, "is_prerelease": false, "epoch": 0}`.
- `version-inspector parse not-a-version` → stderr error, exit code 1.
- `version-inspector compare 1.0.0a1 1.0.0` → `{"result": "less", ...}`.
- `version-inspector check 3.0.0 --specifier ">=2.0,<3.0"` → `{"satisfies": false}`.
- `version-inspector range ">=1.2,<2.0" --versions "1.0,1.2,1.5,2.0,2.5"` → `{"matching": ["1.2", "1.5"]}`.
- `pip install -e ".[dev]"` → installs the package with dev dependencies; `version-inspector --help` is available on PATH.

## Acceptance Criteria

- The package uses `src/` layout with `pyproject.toml` declaring setuptools build backend, all required metadata, dependencies, and a console script entry point.
- `pip install -e .` makes the `version-inspector` command available, and `--help` shows all four subcommands.
- The `parse` command correctly decomposes PEP 440 version strings into their constituent fields including pre-release, post-release, dev, and local segments.
- The `compare` command correctly orders versions including pre-release versions following PEP 440 rules.
- The `check` command validates versions against specifiers and returns correct boolean results.
- The `range` command filters and sorts a version list against a specifier.
- Invalid inputs produce descriptive error messages on stderr with appropriate exit codes.
- Both `json` and `table` output formats work for all commands.
