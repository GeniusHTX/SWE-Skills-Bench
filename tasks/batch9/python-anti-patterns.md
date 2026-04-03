# Task: Refactor Anti-Patterns in Boltons Utility Modules

## Background

The boltons library (https://github.com/mahmoud/boltons) is a collection of pure-Python utility modules. Several modules contain common anti-patterns that reduce maintainability, performance, and safety: mutable default arguments, bare exception handling, type-checking via `isinstance` where duck typing suffices, shadowed builtins, and inefficient data structure usage. This task refactors specific anti-patterns in four modules while preserving all existing public API behavior and passing the existing test suite.

## Files to Create/Modify

- `boltons/cacheutils.py` (modify) — Fix mutable default argument in `LRU.__init__`; replace bare `except:` with specific exception types; add `__slots__` to internal linked-list node class if missing
- `boltons/iterutils.py` (modify) — Replace `isinstance` checks on `list`/`tuple` with protocol-based checks using `collections.abc.Iterable`/`Sequence` where appropriate; fix any functions that shadow builtin names (`input`, `list`, `type`, `id`); replace manual loop accumulation with generator expressions where equivalent
- `boltons/strutils.py` (modify) — Fix mutable default arguments (e.g., default `dict` or `list` parameters); replace string concatenation in loops with `str.join()` or `io.StringIO`; ensure regex patterns are compiled once at module level (not inside frequently-called functions)
- `boltons/dictutils.py` (modify) — Replace any `try/except KeyError` patterns used for flow control with `dict.get()` or `in` checks where clearer; fix any mutable default arguments in public functions
- `tests/test_refactored_anti_patterns.py` (create) — New test file verifying that the refactored code maintains identical behavior for all modified functions, including edge cases

## Requirements

### Mutable Default Arguments

- Audit all function signatures in the four target modules for parameters with mutable defaults (`[]`, `{}`, `set()`)
- Replace each mutable default with `None` and assign the default inside the function body: `if param is None: param = []`
- Specifically fix:
  - `LRU.__init__` and `LRI.__init__` in `cacheutils.py` if they accept dict-like initial data with mutable default
  - Any functions in `strutils.py` that accept a default `list` or `dict` parameter
  - `OrderedMultiDict` methods in `dictutils.py` that use mutable defaults

### Bare Exception Handling

- Find all `except:` or `except Exception:` clauses that silently swallow errors in the four modules
- Replace with specific exception types (`KeyError`, `TypeError`, `ValueError`, `AttributeError`) matching what can actually be raised
- Ensure no anti-pattern of `except Exception as e: pass` remains — at minimum, log or re-raise after cleanup

### Builtin Shadowing

- In `iterutils.py`, find any local variables or parameters named `input`, `list`, `type`, `dict`, `id`, `map`, `filter`, `hash`, `range`, `set`, `all`, `any`, `sum`, `min`, `max`
- Rename them to non-conflicting names with an underscore suffix (e.g., `input_` → `input_val`, `type` → `type_`) while preserving the public API signature (external parameter names must not change; only internal variable names)

### Inefficient Patterns

- In `strutils.py`, find any string building done via repeated `+=` concatenation inside loops and replace with list accumulation + `"".join()`
- In `iterutils.py`, replace any manual `result = []; for x in ...: result.append(f(x)); return result` patterns with list comprehensions where the logic is a simple transformation
- In `cacheutils.py`, ensure `LRU` and `LRI` use `__slots__` on their internal `_Link` node class to reduce memory overhead per cached entry

### Test Coverage

- `tests/test_refactored_anti_patterns.py` must verify:
  - `LRI` and `LRU` function identically after refactoring (insert, get, eviction order)
  - `iterutils.chunked`, `iterutils.unique`, and `iterutils.remap` produce the same outputs as before
  - `strutils.slugify`, `strutils.pluralize`, and `strutils.bytes2human` produce the same outputs as before
  - `dictutils.OrderedMultiDict` insertion, deletion, and iteration produce the same outputs as before
  - No function accepts a shared mutable default (verify by calling twice without arguments and confirming independent instances)

### Expected Functionality

- `LRU(max_size=3)` with 4 insertions evicts the least-recently-used key (same as before)
- `chunked([1,2,3,4,5], 2)` returns `[[1,2],[3,4],[5]]` (same as before)
- `slugify("Hello World!")` returns `"hello_world"` (same as before)
- `OrderedMultiDict([('a',1),('b',2),('a',3)])` maintains insertion order and multi-value access (same as before)
- Existing tests in `tests/test_cacheutils.py`, `tests/test_iterutils.py`, `tests/test_strutils.py`, `tests/test_dictutils.py` all pass without modification

## Acceptance Criteria

- No mutable default arguments remain in any function signature across the four modified modules
- No bare `except:` clauses remain in the four modified modules
- No local variables shadow Python builtins in `iterutils.py`
- String concatenation in loops is replaced with `join()` patterns in `strutils.py`
- `LRI._Link` and `LRU._Link` (or equivalent internal node class) use `__slots__`
- All existing tests pass: `python -m pytest tests/test_cacheutils.py tests/test_iterutils.py tests/test_strutils.py tests/test_dictutils.py -v`
- New tests in `tests/test_refactored_anti_patterns.py` pass: `python -m pytest tests/test_refactored_anti_patterns.py -v`
- `python -m pytest /workspace/tests/test_python_anti_patterns.py -v --tb=short` passes
