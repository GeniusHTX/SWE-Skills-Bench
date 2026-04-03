# Task: Refactor Anti-Patterns in boltons iterutils and fileutils Modules

## Background

The boltons library (https://github.com/mahmoud/boltons) is a collection of pure-Python utilities. The `boltons/iterutils.py` and `boltons/fileutils.py` modules contain several common Python anti-patterns that reduce reliability and maintainability: mutable default arguments, overly broad exception handling, type comparison using `type()` instead of `isinstance()`, mixed I/O and logic, and missing input validation. These modules must be refactored to eliminate these anti-patterns while preserving all existing public API behavior.

## Files to Create/Modify

- `boltons/iterutils.py` (modify) — Fix mutable default arguments, bare except clauses, and type comparison anti-patterns
- `boltons/fileutils.py` (modify) — Fix mutable default arguments, overly broad exception handling, resource management issues, and missing input validation
- `tests/test_iterutils_refactor.py` (create) — Tests verifying that refactored functions maintain identical behavior for valid inputs and properly reject invalid inputs
- `tests/test_fileutils_refactor.py` (create) — Tests verifying fileutils refactored behavior including error handling and resource cleanup

## Requirements

### Mutable Default Arguments

- Identify all function signatures in `iterutils.py` and `fileutils.py` that use mutable default argument values (e.g., `def func(items=[])`  or `def func(mapping={})`).
- Replace every mutable default with `None` and initialize inside the function body:
  ```python
  def func(items=None):
      if items is None:
          items = []
  ```
- The `bucketize` function in `iterutils.py` and the `mkdir_p` function in `fileutils.py` are known to have this pattern.

### Exception Handling

- Replace all bare `except:` and `except Exception:` clauses that silently pass or return `None` with specific exception types.
- In `fileutils.py`, functions that perform file I/O must catch `OSError` (or appropriate subclasses like `FileNotFoundError`, `PermissionError`) instead of catching all exceptions.
- Any caught exception that represents a programming error (`TypeError`, `ValueError`, `AttributeError`) must not be suppressed — it must be re-raised or logged and re-raised.
- In `iterutils.py`, the `first` function and `remap` function must handle `StopIteration` and `TypeError` specifically rather than using generic exception handlers.

### Type Comparison

- Replace all uses of `type(x) == SomeType` and `type(x) is SomeType` with `isinstance(x, SomeType)` when the intent is a type check.
- In `iterutils.py`, the `is_iterable` and `is_scalar` helper functions must use `isinstance` checks for sequences and mappings.
- These changes must correctly handle subclass relationships — e.g., `OrderedDict` must still be recognized as a `dict` subtype.

### Input Validation

- Add validation at function entry points for public API functions:
  - `iterutils.chunked(src, size)` — `size` must be a positive integer; raise `ValueError("size must be a positive integer")` for zero, negative, or non-integer values.
  - `iterutils.windowed(src, size)` — `size` must be a positive integer; raise `ValueError`.
  - `fileutils.atomic_save(dest_path)` — `dest_path` must be a non-empty string; raise `TypeError` if not a string, `ValueError` if empty.
- Validation must occur before any processing or I/O begins.

### Resource Management

- All file operations in `fileutils.py` that open file handles must use `with` statements or equivalent context managers.
- The `atomic_save` context manager must ensure temporary files are cleaned up even when an exception occurs during writing.
- `FilePerms` operations must not leave file descriptors open on error paths.

### Expected Functionality

- `iterutils.chunked([1,2,3,4,5], 2)` → returns `[[1,2], [3,4], [5]]` (unchanged behavior).
- `iterutils.chunked([1,2,3], 0)` → raises `ValueError("size must be a positive integer")`.
- `iterutils.bucketize(range(5), key=lambda x: x % 2)` → returns `{0: [0, 2, 4], 1: [1, 3]}` (unchanged behavior).
- Calling `bucketize` twice without passing `key_as` does not share state between calls (mutable default fixed).
- `fileutils.atomic_save("/some/path")` used as a context manager with an exception during write → temporary file is removed, original file is untouched.
- `fileutils.atomic_save(123)` → raises `TypeError`.
- `iterutils.first([])` → returns `None` (unchanged), does not trigger a bare `except`.

## Acceptance Criteria

- No mutable default arguments remain in any function signature in `iterutils.py` or `fileutils.py`.
- No bare `except:` or `except Exception: pass` clauses remain in either module.
- All type checks use `isinstance()` rather than `type()` comparison.
- Public API functions `chunked`, `windowed`, and `atomic_save` validate their inputs and raise specific exceptions with descriptive messages for invalid arguments.
- All file handle operations use context managers ensuring cleanup on error paths.
- All existing tests in the boltons test suite continue to pass after refactoring.
- New tests verify that invalid inputs are rejected and that mutable default state is not shared across calls.
