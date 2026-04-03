# Task: Refactor boltons iterutils and cacheutils to Eliminate Anti-Patterns

## Background

boltons (https://github.com/mahmoud/boltons) is a widely-used Python utility library. The `iterutils.py` and `cacheutils.py` modules contain several longstanding code patterns that hinder maintainability and reliability: bare exception handlers, mutable default arguments, redundant retry logic scattered across functions, and resource handles that are not properly released. This task requires refactoring these two modules to eliminate these specific issues while preserving all existing public API behavior.

## Files to Create/Modify

- `boltons/iterutils.py` (modify) — Fix bare `except:` clauses, mutable default arguments, and redundant type-checking code in `chunked`, `chunked_iter`, `bucketize`, and `unique`.
- `boltons/cacheutils.py` (modify) — Fix timeout/retry duplication in `LRU` and `LRI` cache classes, replace bare `except:` with specific exception types, and ensure file-backed caches release handles on error.
- `tests/test_iterutils.py` (modify) — Add test cases that verify the refactored behavior for edge cases: empty iterables, `None` values, generators that raise mid-iteration.
- `tests/test_cacheutils.py` (modify) — Add test cases for cache eviction edge cases, concurrent access patterns, and cleanup-on-error scenarios.

## Requirements

### iterutils.py Fixes

- `chunked(iterable, size)`: Replace the bare `except:` clause in the iteration fallback path with `except (TypeError, AttributeError):` (the actual exceptions that a non-iterable input produces).
- `bucketize(iterable, key, ...)`: The `key_func` default parameter must not use a mutable container as its default value; use `None` and assign inside the function body.
- `unique(iterable, key=None)`: If the input `key` callable raises an exception on a specific element, the exception must propagate instead of being silently swallowed; remove any generic exception suppression.
- All functions must still accept generators (single-pass iterables) and standard sequences identically.

### cacheutils.py Fixes

- `LRI` (Least Recently Inserted) cache: The `__setitem__` method catches `Exception` broadly when evicting old entries; narrow this to `KeyError`.
- `LRU` (Least Recently Used) cache: If a `on_miss` callback is configured and raises an exception, the cache must not leave a partial entry in the internal data structures; the state must roll back.
- Any file I/O operations (if present in cache serialization paths) must use context managers or `try/finally` to ensure file handles are closed on exceptions.
- The `soft_miss` feature must not silently mask `KeyboardInterrupt` or `SystemExit`.

### Expected Functionality

- `chunked("not-a-sequence", 3)` still works by falling back to iteration, but `chunked(42, 3)` raises `TypeError` instead of returning an empty list silently.
- `bucketize([], key=lambda x: x)` returns `{}` (not an error).
- `unique([1, 2, None, 1, None])` returns `[1, 2, None]` (None values handled correctly).
- `LRU(max_size=2)` after inserting 3 items has `len() == 2` and the first-inserted item is evicted.
- An `on_miss` callback that raises `ValueError` does not leave a ghost entry in the LRU cache.

## Acceptance Criteria

- No bare `except:` or `except Exception:` clauses remain in `iterutils.py` or `cacheutils.py`; all exception handlers catch specific exception types.
- No mutable default arguments (lists, dicts, sets) appear in any function signatures in the modified files.
- `LRU` and `LRI` cache classes clean up internal state when operations fail mid-way.
- All existing tests in `tests/test_iterutils.py` and `tests/test_cacheutils.py` continue to pass.
- New test cases cover the edge cases listed above and at least one error-propagation scenario per module.
- The public API (function signatures, return types) of both modules remains unchanged.
