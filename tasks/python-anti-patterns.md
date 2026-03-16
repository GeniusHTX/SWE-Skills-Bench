# Task: Refactor boltons Core Modules to Modern Python Patterns

## Background

The `boltons/iterutils.py` and `boltons/strutils.py` modules contain legacy Python patterns that should be modernized to Python 3.9+ idioms while maintaining backward compatibility.

## Files to Modify

- `boltons/iterutils.py` - Refactor to modern Python patterns
- `boltons/strutils.py` - Refactor to modern Python patterns

## Requirements

### iterutils.py Improvements
- Replace old-style `str.format()` calls with f-strings where applicable
- Replace manual type checks (`type(x) == ...`) with `isinstance()` calls
- Use walrus operator (`:=`) where it simplifies assignments in conditionals
- Replace `dict()` calls with dict literals `{}`
- Use modern `dict | dict` union operator where merging dicts (Python 3.9+)

### strutils.py Improvements
- Convert `str.format()` to f-string formatting
- Replace bare `except:` clauses with explicit exception types
- Use `isinstance()` for type guards instead of `type() ==`
- Simplify comprehensions where possible (avoid unnecessary list wrapping)
- Use generator expressions instead of list comprehensions for memory efficiency where the list is not reused

### Constraints
- All existing tests must continue to pass
- Do not change public API signatures
- Maintain backward compatibility with Python 3.9+

## Acceptance Criteria

- `boltons/iterutils.py` and `boltons/strutils.py` compile without syntax errors
- All modernization changes follow PEP 8 and Python 3.9+ conventions
- Existing functionality is preserved
