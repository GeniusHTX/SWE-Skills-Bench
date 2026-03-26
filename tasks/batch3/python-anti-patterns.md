# Task: Refactor cacheutils Module to Eliminate Common Anti-Patterns

## Background

The boltons library (https://github.com/mahmoud/boltons) is a collection of pure-Python utility modules that extend the standard library. The `boltons/cacheutils.py` module provides caching utilities including `LRU`, `LRI`, and `cachedproperty`. Several functions in this module exhibit common Python anti-patterns — scattered error handling, mutable default arguments, overly broad exception catches, type-unsafe APIs, and missing resource cleanup — that reduce reliability and maintainability.

## Files to Create/Modify

- `boltons/cacheutils.py` (modify) — Refactor to fix anti-patterns: mutable defaults, bare excepts, missing type hints, inconsistent error handling
- `tests/test_cacheutils_refactor.py` (create) — Tests verifying refactored behavior, edge cases, error paths, and type safety

## Requirements

### Mutable Default Arguments

- Identify and fix any function signatures that use mutable default arguments (e.g., `def func(items=[])`)
- Replace with `None` sentinel and create a fresh instance inside the function body
- Ensure callers that relied on the shared mutable default still work correctly

### Exception Handling

- Replace any bare `except:` or `except Exception:` clauses with specific exception types
- Ensure `KeyError`, `TypeError`, and `ValueError` are caught separately where appropriate
- Add meaningful error messages to raised exceptions that include the offending value and expected type
- Do not silence exceptions that indicate programmer errors (e.g., `TypeError` from wrong argument type)

### Type Safety and Validation

- Add input validation to public API methods on `LRU` and `LRI` classes:
  - `max_size` must be a positive integer; raise `ValueError` with message if not
  - Cache keys must be hashable; raise `TypeError` with descriptive message if not
  - `on_miss` callback (if provided) must be callable; raise `TypeError` if not
- Add Python type annotations to all public methods and the `__init__` signatures of `LRU`, `LRI`, and `cachedproperty`

### Resource and State Management

- Ensure `LRU` and `LRI` are safe to use in multithreaded contexts by documenting thread-safety guarantees (or lack thereof) in docstrings
- Ensure `cachedproperty` correctly handles the case where the descriptor is accessed on the class itself (not an instance) — it should return the descriptor object, not raise `AttributeError`
- Ensure cache eviction in `LRU` fires consistently when the cache exceeds `max_size`, including when items are added via `__setitem__` and `update()`

### Expected Functionality

- `LRU(max_size=0)` raises `ValueError` with a message indicating max_size must be positive
- `LRU(max_size=5)` followed by inserting 10 items retains only the 5 most recently accessed items
- `LRI(on_miss="not_callable")` raises `TypeError`
- Accessing `MyClass.cached_prop` on the class (not an instance) returns the `cachedproperty` descriptor
- `lru[unhashable_list]` raises `TypeError` with a message mentioning the key type
- All existing `boltons/tests/test_cacheutils.py` tests continue to pass after refactoring

## Acceptance Criteria

- No mutable default arguments remain in any function signature in `cacheutils.py`
- No bare `except:` or overly broad `except Exception:` clauses remain; all catches are specific
- Public API methods on `LRU`, `LRI`, and `cachedproperty` have Python type annotations
- Input validation raises `ValueError` or `TypeError` with descriptive messages for invalid arguments
- `cachedproperty` returns the descriptor when accessed on the class rather than an instance
- Cache eviction behavior is consistent across all insertion methods (`__setitem__`, `update`, `setdefault`)
- Existing tests continue to pass and new tests cover the refactored validation and edge cases
