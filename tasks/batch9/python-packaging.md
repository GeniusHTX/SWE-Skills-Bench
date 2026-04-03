# Task: Create a Reusable Python CLI Package with Modern Packaging Standards

## Background

The packaging library (https://github.com/pypa/packaging) demonstrates Python packaging best practices. A new reference package is needed that showcases a complete, modern Python package using the `src` layout, `pyproject.toml` with setuptools backend, CLI entry points, optional dependency groups, version management, and proper test configuration. The package implements a simple "code metrics" CLI tool that analyzes Python files for complexity metrics.

## Files to Create/Modify

- `examples/code-metrics/pyproject.toml` (create) — Full `pyproject.toml` with PEP 621 metadata, setuptools backend, entry points, optional dependencies, and tool configuration for pytest, mypy, ruff
- `examples/code-metrics/src/code_metrics/__init__.py` (create) — Package init with `__version__` and public API exports
- `examples/code-metrics/src/code_metrics/analyzer.py` (create) — `CodeAnalyzer` class that computes lines of code, cyclomatic complexity, function count, class count, import count, and docstring coverage for Python files
- `examples/code-metrics/src/code_metrics/cli.py` (create) — CLI using `argparse` with subcommands: `analyze` (single file), `report` (directory), `compare` (two files). Entry point registered as `code-metrics` console script
- `examples/code-metrics/src/code_metrics/formatters.py` (create) — Output formatters: `TableFormatter`, `JSONFormatter`, `CSVFormatter` implementing a `Formatter` protocol
- `examples/code-metrics/README.md` (create) — Usage documentation with installation and CLI examples
- `examples/code-metrics/tests/conftest.py` (create) — Shared test fixtures: sample Python files with known metrics
- `examples/code-metrics/tests/test_analyzer.py` (create) — Tests for all analyzer metrics with known-value assertions
- `examples/code-metrics/tests/test_cli.py` (create) — CLI integration tests using subprocess

## Requirements

### pyproject.toml

- `[build-system]`: requires `setuptools>=68.0` and `setuptools-scm>=8.0`, backend `setuptools.build_meta`
- `[project]`: name `code-metrics`, version `0.1.0`, requires-python `>=3.10`, license `MIT`
- `[project.dependencies]`: no runtime dependencies (stdlib only)
- `[project.optional-dependencies]`:
  - `dev`: `["pytest>=7.0", "pytest-cov>=4.0", "mypy>=1.0", "ruff>=0.1.0"]`
  - `rich`: `["rich>=13.0"]` (for rich table output)
- `[project.scripts]`: `code-metrics = "code_metrics.cli:main"`
- `[project.entry-points."code_metrics.formatters"]`: register `table`, `json`, `csv` as plugin entry points
- `[tool.setuptools.packages.find]`: where `["src"]`
- `[tool.pytest.ini_options]`: `testpaths = ["tests"]`, `addopts = "--strict-markers"`
- `[tool.mypy]`: `strict = true`
- `[tool.ruff]`: `target-version = "py310"`, `line-length = 88`

### Code Analyzer (`analyzer.py`)

- Class `CodeAnalyzer` with method `analyze(source: str) -> FileMetrics`:
- `FileMetrics` dataclass: `lines_of_code` (int, non-blank non-comment lines), `total_lines` (int), `blank_lines` (int), `comment_lines` (int), `function_count` (int), `class_count` (int), `import_count` (int), `cyclomatic_complexity` (int, total across all functions), `docstring_coverage` (float, fraction of functions/classes with docstrings), `average_function_length` (float, lines per function)
- Use `ast` module to parse the source and walk the AST:
  - Count `FunctionDef`, `AsyncFunctionDef` for function_count
  - Count `ClassDef` for class_count
  - Count `Import`, `ImportFrom` for import_count
  - Cyclomatic complexity: count `if`, `elif`, `for`, `while`, `except`, `with`, `and`, `or`, `assert` nodes + 1 per function
  - Docstring coverage: check if first statement of each function/class is an `Expr(value=Constant(value=str))`
- Method `analyze_file(path: Path) -> FileMetrics` — Reads file and calls `analyze()`
- Method `analyze_directory(path: Path, pattern: str = "**/*.py") -> dict[str, FileMetrics]` — Analyzes all matching files, returns dict keyed by relative path

### CLI (`cli.py`)

- `code-metrics analyze <file>` — Print metrics for a single file, default table format
- `code-metrics report <directory> [--format table|json|csv] [--sort-by complexity|lines|docstring_coverage]` — Print metrics for all Python files in directory
- `code-metrics compare <file1> <file2>` — Show side-by-side metrics comparison with delta column
- `--format` flag accepts `table` (default), `json`, `csv`
- `--output` flag writes to file instead of stdout
- Exit code 0 on success, 1 on error, 2 on invalid arguments

### Formatters (`formatters.py`)

- `Formatter` protocol: `def format(metrics: dict[str, FileMetrics]) -> str`
- `TableFormatter` — ASCII table with columns: File, LOC, Functions, Classes, Complexity, Docstring%, sorted by first column
- `JSONFormatter` — Pretty-printed JSON with 2-space indent
- `CSVFormatter` — RFC 4180 compliant CSV with header row

### Expected Functionality

- `pip install -e ".[dev]"` installs the package with dev dependencies
- `code-metrics analyze src/code_metrics/analyzer.py` prints metrics table for that file
- `code-metrics report src/ --format json --sort-by complexity` outputs sorted JSON metrics
- `code-metrics compare file1.py file2.py` shows delta for each metric
- Analyzing a file with 3 functions (2 with docstrings, 1 without) reports docstring_coverage = 0.667

## Acceptance Criteria

- `pyproject.toml` validates against PEP 621 and is buildable with `python -m build`
- `pip install -e .` succeeds and registers the `code-metrics` console script
- `code-metrics analyze` correctly computes all metrics using AST analysis
- Cyclomatic complexity counts match the formula: branches + boolean operators + 1 per function
- Docstring coverage correctly identifies functions/classes with and without docstrings
- All three formatters produce valid output (parseable JSON, valid CSV)
- `python -m pytest tests/ -v` passes all tests
- `python -m pytest /workspace/tests/test_python_packaging.py -v --tb=short` passes
