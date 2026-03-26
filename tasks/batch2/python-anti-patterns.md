# Task: Refactor Python Anti-Patterns in the Boltons Library

## Background

Boltons (https://github.com/mahmoud/boltons) is a set of pure-Python utility libraries. Some modules contain legacy coding patterns that could be modernized to improve readability, performance, and maintainability. The task is to identify and refactor anti-patterns in specific modules.

## Files to Modify

- `boltons/iterutils.py` — Iterator utility functions
- `boltons/strutils.py` — String utility functions

## Requirements

### Modernization Targets

- Replace manual type checking patterns (e.g., `type(x) == ...`) with `isinstance()` calls where appropriate
- Convert old-style string formatting (`%` operator or `.format()`) to f-strings where it improves readability
- Replace bare `except:` clauses with specific exception types
- Simplify any overly verbose conditional logic or loops that could use more Pythonic constructs (e.g., comprehensions, `any()`/`all()`, walrus operator where beneficial)

### Constraints

- All changes must preserve the existing public API and behavior of both modules
- Do not rename any public functions, classes, or parameters
- Each refactored pattern should make the code more idiomatic without sacrificing clarity
- Both files must remain syntactically valid Python after modification

## Expected Functionality

- All existing functionality and return values remain identical after refactoring
- The refactored code is more concise and follows modern Python idioms
- No new dependencies are introduced

## Acceptance Criteria

- The targeted modules are refactored to use more idiomatic Python constructs without changing their public APIs.
- Manual type equality checks, overly broad exception handling, and outdated string-formatting patterns are removed where appropriate.
- Refactoring improves readability and maintainability rather than merely changing style mechanically.
- Existing behavior and return values remain unchanged for the covered utility functions.
- The resulting code remains dependency-free and consistent with the surrounding Boltons style.
