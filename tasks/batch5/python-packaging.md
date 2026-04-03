# Task: Create a pyproject.toml-Based Package with CLI and Version Management for packaging

## Background

The `packaging` library (https://github.com/pypa/packaging) provides version parsing and specifier utilities used across the Python ecosystem. This task requires creating a companion CLI tool (`packaging-cli`) as a distributable Python package within the repository, complete with a `pyproject.toml` build configuration, CLI entry points, automated version management, and proper package structure.

## Files to Create/Modify

- `packaging_cli/pyproject.toml` (create) — PEP 621 project metadata, build system configuration (using `hatchling` or `setuptools` as build backend), CLI entry point, and dependency declarations.
- `packaging_cli/src/packaging_cli/__init__.py` (create) — Package init with `__version__` variable.
- `packaging_cli/src/packaging_cli/cli.py` (create) — CLI entry point implementing `packaging-cli check-version <version_string>`, `packaging-cli check-specifier <specifier> <version>`, and `packaging-cli normalize <version>`.
- `packaging_cli/src/packaging_cli/commands/version_check.py` (create) — Logic for parsing and validating version strings using `packaging.version`.
- `packaging_cli/src/packaging_cli/commands/specifier_check.py` (create) — Logic for checking if a version satisfies a specifier using `packaging.specifiers`.
- `packaging_cli/src/packaging_cli/commands/normalize.py` (create) — Logic for normalizing PEP 440 version strings.
- `packaging_cli/tests/test_cli.py` (create) — Tests for all three CLI commands with valid inputs, invalid inputs, and edge cases.
- `packaging_cli/README.md` (create) — Usage documentation for the CLI tool.

## Requirements

### Package Structure

- Use the `src/` layout: source code lives under `packaging_cli/src/packaging_cli/`.
- `pyproject.toml` must define: `name = "packaging-cli"`, `version` (use dynamic version from `__init__.py` or `pyproject.toml`), `requires-python >= "3.9"`, `dependencies = ["packaging>=23.0"]`.
- Build backend must be explicitly declared (e.g., `hatchling` or `setuptools` with `build-system` table).
- A `[project.scripts]` entry must define `packaging-cli` pointing to `packaging_cli.cli:main`.

### CLI Commands

- `packaging-cli check-version "1.2.3"` → prints `Valid PEP 440 version: 1.2.3` and exits 0.
- `packaging-cli check-version "not.a" ` → prints `Invalid version: 'not.a'` to stderr and exits 1.
- `packaging-cli check-specifier ">=1.0,<2.0" "1.5.0"` → prints `1.5.0 matches >=1.0,<2.0` and exits 0.
- `packaging-cli check-specifier ">=2.0" "1.5.0"` → prints `1.5.0 does not match >=2.0` and exits 1.
- `packaging-cli normalize "1.02.003"` → prints `1.2.3` (normalized form).
- `packaging-cli normalize "v1.0-alpha"` → prints the PEP 440 normalized form or an error if un-normalizable.

### Edge Cases

- Pre-release versions (`1.0a1`, `1.0.dev3`) must be handled correctly by all commands.
- Post-release (`1.0.post1`), local (`1.0+local`), and epoch (`1!1.0`) versions must be parseable.
- Empty string input → exit code 1 with appropriate error message.
- `--help` flag prints usage information for each command.

### Expected Functionality

- `pip install -e ./packaging_cli` succeeds and makes the `packaging-cli` command available.
- `pip wheel ./packaging_cli` produces a `.whl` file with correct metadata.
- `packaging-cli check-version "21.3"` → exit 0, `packaging-cli check-version "abc"` → exit 1.
- `packaging-cli check-specifier "~=1.4" "1.4.2"` → exit 0 (compatible release match).

## Acceptance Criteria

- `pyproject.toml` is valid PEP 621 with a declared build backend, dependencies, and CLI entry point.
- `pip install -e ./packaging_cli` installs successfully and registers the `packaging-cli` command.
- All three CLI commands (`check-version`, `check-specifier`, `normalize`) produce correct output and exit codes for valid and invalid inputs.
- Pre-release, post-release, local, and epoch version strings are handled correctly.
- Tests cover valid inputs, invalid inputs, pre-release edge cases, and `--help` output for each command.
- `pip wheel ./packaging_cli` produces a valid wheel file.
