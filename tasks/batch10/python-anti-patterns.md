# Task: Refactor Anti-Patterns in boltons Utility Modules

## Background

The boltons utility library (`mahmoud/boltons`) contains several modules under `boltons/` that have accumulated code-quality issues over time. Three modules — `boltons/socketutils.py`, `boltons/iterutils.py`, and `boltons/fileutils.py` — need targeted refactoring to eliminate error-handling anti-patterns, separate I/O from logic, close resource leaks, and add missing type annotations. The refactored code must remain backward-compatible: all existing public APIs must keep their signatures and return types.

## Files to Create/Modify

- `boltons/socketutils.py` (modify) — Fix bare exception handlers, centralize timeout/retry logic, add type annotations to public functions
- `boltons/iterutils.py` (modify) — Separate I/O-dependent utility functions from pure logic, fix untyped collection returns, add type annotations
- `boltons/fileutils.py` (modify) — Close resource leaks (unclosed file handles), replace bare `except` blocks with specific exception types, validate inputs at function boundaries
- `tests/test_socketutils_refactor.py` (create) — Tests for refactored socket utilities covering error paths, timeout behavior, and resource cleanup
- `tests/test_iterutils_refactor.py` (create) — Tests for refactored iteration utilities covering batch processing failures, edge cases (empty input, single element, None values)
- `tests/test_fileutils_refactor.py` (create) — Tests for refactored file utilities covering resource cleanup, invalid input rejection, and partial-failure handling

## Requirements

### Error Handling in socketutils.py

- Replace every bare `except Exception` or `except:` block with specific exception types (`socket.timeout`, `socket.error`, `ConnectionError`, `OSError`)
- Every caught exception must be logged with the exception type and message before being re-raised or converted to a domain-specific error
- No `except` block may silently swallow an exception (no bare `pass` in any `except`)
- Timeout values must not be hardcoded in individual functions; extract them into module-level constants or accept them as function parameters with defaults

### I/O Separation in iterutils.py

- Any function that currently mixes data fetching with transformation logic must be split: one function performs I/O (or accepts data as input), another performs the pure transformation
- Batch-processing functions must not abort on the first error; they must collect both successes and failures and return a result object or tuple `(succeeded: list, failed: list[tuple[int, Exception]])` where the int is the item index
- All public functions must have complete type annotations: parameter types, return types, and generic type variables where applicable (e.g., `T = TypeVar('T')`)
- Functions returning collections must use parameterized types (`list[T]`, `dict[str, T]`) not bare `list` or `dict`

### Resource Management in fileutils.py

- Every file open operation must use a context manager (`with` statement); no `open()` call may exist outside a `with` block
- Any function that opens multiple files must ensure all are closed even if an intermediate operation raises an exception
- Add input validation at the top of every public function: check that file paths are non-empty strings, that mode parameters are valid, and raise `ValueError` with a descriptive message for invalid inputs
- Functions that accept a `path` parameter must validate that the path is a `str` or `os.PathLike` before proceeding

### Type Annotations

- Every public function across all three modules must have full type annotations
- Use `from __future__ import annotations` at the top of each modified module
- Generic functions must use `TypeVar` with appropriate bounds
- Return types must never be bare `list`, `dict`, `tuple`, or `None` — always parameterized

### Expected Functionality

- `socketutils.BufferedSocket.recv` with a 0.001s timeout on a non-responsive target → raises `socket.timeout` (not a generic `Exception`)
- `iterutils.chunked([], 5)` → returns `[]` (empty input handled without error)
- `iterutils.chunked([1,2,3], 0)` → raises `ValueError` with message containing "chunk size"
- `iterutils.chunked(range(10), 3)` → returns `[[0,1,2],[3,4,5],[6,7,8],[9]]` (last chunk is partial)
- A batch-processing function given `[valid, invalid, valid]` → returns successes for indices 0 and 2, failure for index 1 with the captured exception
- `fileutils.atomic_save("/some/path")` used as context manager properly cleans up temp files even when the body raises an exception
- `fileutils.iter_find_files` with a non-existent base directory → raises `FileNotFoundError` (not a bare `OSError` or silenced error)
- Calling any public function with `path=None` → raises `ValueError` before any I/O occurs
- Calling any public function with `path=""` → raises `ValueError` with a message referencing "path"

## Acceptance Criteria

- `python -m pytest tests/test_socketutils_refactor.py -v` passes with all tests green
- `python -m pytest tests/test_iterutils_refactor.py -v` passes with all tests green
- `python -m pytest tests/test_fileutils_refactor.py -v` passes with all tests green
- Zero bare `except:` or `except Exception: pass` patterns remain in the three modified modules (verifiable via `grep -rn "except.*pass" boltons/socketutils.py boltons/iterutils.py boltons/fileutils.py`)
- Every `open()` call in `fileutils.py` is inside a `with` statement
- `mypy boltons/socketutils.py boltons/iterutils.py boltons/fileutils.py --ignore-missing-imports` reports zero errors
- All existing boltons tests continue to pass (`python -m pytest tests/ -v`) — no regressions in public API behavior
