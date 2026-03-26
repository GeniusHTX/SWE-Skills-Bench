# Task: Create a Python Package with CLI, src Layout, and Publish Workflow for pypa/packaging

## Background

The pypa/packaging project (https://github.com/pypa/packaging) provides core utilities for Python packaging. This task adds a new companion CLI tool package (`packaging-cli`) within the repository that wraps common packaging operations (version parsing, requirement resolution, metadata inspection) into a command-line interface. The package must follow modern Python packaging standards with a src layout, proper metadata, and an automated publish workflow.

## Files to Create/Modify

- `src/packaging_cli/__init__.py` (create) — Package init with `__version__`
- `src/packaging_cli/__main__.py` (create) — Entry point for `python -m packaging_cli`
- `src/packaging_cli/cli.py` (create) — CLI commands: `parse-version`, `check-requirement`, `inspect-metadata`
- `src/packaging_cli/py.typed` (create) — PEP 561 marker file
- `pyproject.toml` (modify) — Add packaging-cli project metadata, entry points, and build configuration
- `tests/test_cli.py` (create) — Tests for all CLI commands including edge cases and error handling
- `.github/workflows/publish.yml` (create) — GitHub Actions workflow to build and publish to PyPI on tag push

## Requirements

### Package Structure

- Use `src/` layout: all source code under `src/packaging_cli/`
- Define package metadata in `pyproject.toml` using the `[project]` table: name `packaging-cli`, version matching `__version__`, description, license (BSD-2-Clause or Apache-2.0), `requires-python >= 3.9`, and dependencies including `packaging >= 24.0`
- Configure build backend (setuptools or hatchling) in `[build-system]`
- Define a console script entry point: `packaging-cli = packaging_cli.cli:main`

### CLI Commands

- `packaging-cli parse-version <version_string>` — Parse a PEP 440 version string and output its components as JSON: `{"major": int, "minor": int, "micro": int, "pre": ..., "post": ..., "dev": ..., "is_prerelease": bool, "is_postrelease": bool, "is_devrelease": bool}`; exit code 0 on success; if the version string is invalid, print an error message to stderr and exit with code 1
- `packaging-cli check-requirement <requirement_string>` — Parse a PEP 508 requirement string and output: `{"name": str, "extras": [...], "specifier": str, "url": str|null, "marker": str|null}`; exit code 0 on valid requirement; exit code 1 with error message on invalid input
- `packaging-cli inspect-metadata <path_to_wheel_or_sdist>` — Read metadata from a `.whl` or `.tar.gz` file and output: `{"name": str, "version": str, "summary": str, "requires_python": str, "dependencies": [...]}`; exit code 0 on success; exit code 1 if the file does not exist or is not a valid distribution
- All commands must accept `--format` flag with values `json` (default) and `text` (human-readable table format)
- Global `--help` and per-command `--help` must be available

### Publish Workflow

- Trigger on push of tags matching `v*`
- Build the package using `python -m build`
- Publish to PyPI using `pypa/gh-action-pypi-publish@release/v1`
- Use OIDC trusted publishing (no API token secrets needed; uses `id-token: write` permission)
- Include a test step that runs `pytest` before publishing (fail-fast: do not publish if tests fail)

### Expected Functionality

- `packaging-cli parse-version "3.2.1"` outputs `{"major": 3, "minor": 2, "micro": 1, "pre": null, "post": null, "dev": null, "is_prerelease": false, ...}`
- `packaging-cli parse-version "not-a-version"` prints `"Error: Invalid version: 'not-a-version'"` to stderr and exits with code 1
- `packaging-cli check-requirement "requests>=2.28,<3.0"` outputs the parsed requirement JSON
- `packaging-cli check-requirement ""` exits with code 1
- `packaging-cli inspect-metadata dist/packaging_cli-0.1.0-py3-none-any.whl` outputs valid metadata JSON
- `packaging-cli inspect-metadata nonexistent.whl` exits with code 1 mentioning the file was not found
- `pip install -e .` from the repository root installs the `packaging-cli` command

## Acceptance Criteria

- The package uses a `src/` layout with all source under `src/packaging_cli/`
- `pyproject.toml` contains valid `[project]` metadata, `[build-system]`, and `[project.scripts]` entry point
- `packaging-cli parse-version`, `check-requirement`, and `inspect-metadata` commands produce correct JSON output for valid inputs
- Invalid inputs result in exit code 1 with descriptive error messages on stderr
- Both `--format json` and `--format text` produce correctly formatted output
- `python -m packaging_cli` works as an alternative invocation
- `py.typed` marker file is present for PEP 561 compliance
- The GitHub Actions publish workflow triggers on version tags, runs tests, builds, and publishes using OIDC trusted publishing
- Tests cover valid inputs, invalid inputs, edge cases (pre-release versions, extras, markers), and file-not-found scenarios
