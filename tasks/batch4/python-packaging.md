# Task: Create a Distributable Python Package with CLI, Plugins, and PyPI-Ready Configuration

## Background

The packaging repository (https://github.com/pypa/packaging) provides core utilities for Python packaging. A new example package is needed that demonstrates a production-ready Python package structure using the modern `pyproject.toml` configuration, a source layout (`src/`), a CLI entry point, a plugin system with entry points, comprehensive metadata, and build/publish tooling — serving as a reference implementation for Python library authors.

## Files to Create/Modify

- `examples/sample_package/pyproject.toml` (create) — Complete pyproject.toml with build system, metadata, dependencies, optional extras, entry points, and tool config
- `examples/sample_package/src/sample_lib/__init__.py` (create) — Package init with version and public API exports
- `examples/sample_package/src/sample_lib/core.py` (create) — Core library functionality: a `TextProcessor` class with tokenize, normalize, and statistics methods
- `examples/sample_package/src/sample_lib/cli.py` (create) — CLI entry point using argparse: `sample-tool process`, `sample-tool stats`, `sample-tool plugins`
- `examples/sample_package/src/sample_lib/plugins.py` (create) — Plugin discovery and registration system using `importlib.metadata` entry points
- `examples/sample_package/src/sample_lib/py.typed` (create) — PEP 561 marker for typed package
- `examples/sample_package/tests/__init__.py` (create) — Test package init
- `examples/sample_package/tests/test_core.py` (create) — Tests for TextProcessor
- `examples/sample_package/tests/test_cli.py` (create) — Tests for CLI commands
- `examples/sample_package/tests/test_plugins.py` (create) — Tests for plugin system
- `examples/sample_package/README.md` (create) — Package README with installation, usage, and plugin development guide

## Requirements

### pyproject.toml

- Build system: `setuptools>=61.0` with `setuptools.build_meta` backend
- Project metadata: name `"sample-lib"`, version `"1.0.0"`, description, authors, license (MIT), requires-python `">=3.9"`, classifiers (at least 5 relevant ones)
- Dependencies: none required for core (pure Python)
- Optional dependencies: `dev` (pytest, mypy, ruff), `docs` (sphinx, myst-parser)
- Entry points: `[project.scripts]` section with `sample-tool = "sample_lib.cli:main"`
- Plugin entry points: `[project.entry-points."sample_lib.plugins"]` section with a built-in `"uppercase"` plugin
- Tool config: `[tool.pytest.ini_options]` with testpaths and `[tool.mypy]` with strict mode
- `[tool.setuptools.packages.find]` with `where = ["src"]`

### TextProcessor Class (core.py)

- Constructor accepts: `text` (str)
- `tokenize() -> list[str]` — splits text into tokens by whitespace and punctuation; strips empty tokens
- `normalize(lowercase: bool = True, strip_punctuation: bool = True) -> str` — returns normalized text
- `word_count() -> int` — number of tokens
- `char_count(include_spaces: bool = False) -> int` — character count
- `unique_words() -> set[str]` — set of unique lowercased tokens
- `word_frequencies() -> dict[str, int]` — frequency count of each lowercased token, sorted by frequency descending
- `top_words(n: int = 10) -> list[tuple[str, int]]` — top N most frequent words
- `sentences() -> list[str]` — splits by sentence-ending punctuation (`.`, `!`, `?`) preserving the delimiter
- Must handle empty string input without error (return empty lists/dicts/0 counts)

### CLI (cli.py)

- `main()` function as the entry point
- `sample-tool process <file_or_text> [--lowercase] [--strip-punctuation] [--output FORMAT]` — processes text and outputs normalized result; `--output` supports `"text"` (default) and `"json"`
- `sample-tool stats <file_or_text> [--top N]` — shows word count, char count, unique words, and top N words
- `sample-tool plugins [--list]` — lists all discovered plugins with their descriptions
- When `<file_or_text>` is a path to an existing file, read its contents; otherwise treat the argument as literal text
- Exit code 0 on success, 1 on error with a message to stderr

### Plugin System (plugins.py)

- `PluginManager` class
- `discover() -> list[PluginInfo]` — discovers plugins registered under the `"sample_lib.plugins"` entry point group using `importlib.metadata.entry_points()`; returns `PluginInfo` objects with `name`, `description`, `transform_fn`
- `register(name: str, transform_fn: callable, description: str = "")` — manually registers a plugin at runtime
- `apply(name: str, text: str) -> str` — applies the named plugin's `transform_fn` to the text; raises `KeyError` if the plugin is not found
- `list_plugins() -> list[str]` — returns sorted list of registered plugin names
- Built-in `"uppercase"` plugin: transforms text to uppercase
- Each plugin must be a callable with signature `(text: str) -> str`

### Expected Functionality

- `pip install -e ".[dev]"` installs the package in development mode with test dependencies
- `sample-tool process "Hello, World!" --lowercase` outputs `"hello world"`
- `sample-tool stats "the quick brown fox jumps over the lazy dog"` outputs word count 9, unique words 9, top words with count 1 each
- `sample-tool plugins --list` shows at least the built-in `"uppercase"` plugin
- `python -m build` produces a wheel and sdist in `dist/`
- `pytest` runs all tests from the project root successfully

## Acceptance Criteria

- `pyproject.toml` is valid and contains all required sections: build-system, project metadata, dependencies, optional deps, scripts entry point, plugin entry points, and tool configuration
- Package follows source layout with `src/sample_lib/` and includes `py.typed` marker
- `TextProcessor` correctly tokenizes, normalizes, counts, and computes word frequencies for arbitrary text input
- CLI supports `process`, `stats`, and `plugins` subcommands with correct argument parsing and output formats
- Plugin system discovers entry-point-based plugins, supports runtime registration, and applies transforms
- All tests pass covering core functionality, CLI commands, and plugin discovery/registration
- `python -m build` produces valid wheel and sdist artifacts
