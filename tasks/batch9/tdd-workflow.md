# Task: Implement String Calculator Features Using Test-Driven Development

## Background

The TDD starter project (https://github.com/tdd-starters/python) provides a minimal Python package with a string-based calculator in `src/python_starter/calculator.py`. The current implementation handles basic arithmetic expressions. The task is to extend the calculator with three new capabilities — support for parenthesized sub-expressions, a modulo operator (`%`), and a unary negation prefix (`-`) — following a strict test-first workflow where every new behavior is covered by tests before the implementation exists.

## Files to Create/Modify

- `tests/test_calculator.py` (modify) — Add parameterized test cases for parenthesized expressions, modulo operations, and unary negation before implementing the features
- `src/python_starter/calculator.py` (modify) — Extend the `evaluate` function to handle parentheses, `%`, and unary `-`
- `src/python_starter/__init__.py` (modify) — Ensure the updated `evaluate` function is re-exported if the public API changes

## Requirements

### Parenthesized Expressions

- The `evaluate` function must support arbitrarily nested parentheses: e.g., `evaluate("(2 + 3) * 4")` → `20`
- Parentheses must override normal operator precedence: `evaluate("2 * (3 + 4)")` → `14`
- Nested parentheses must evaluate correctly: `evaluate("((1 + 2) * (3 + 4))")` → `21`
- Mismatched parentheses must raise a `ValueError` with a message indicating the mismatch position
- Empty parentheses `evaluate("()")` must raise a `ValueError`

### Modulo Operator

- The `%` operator must be supported with the same precedence as multiplication and division: `evaluate("10 % 3")` → `1`
- Modulo by zero must raise a `ValueError` (not `ZeroDivisionError`): `evaluate("5 % 0")` → `ValueError`
- Modulo must work with other operators: `evaluate("10 + 7 % 3")` → `11`

### Unary Negation

- A leading minus must negate the first operand: `evaluate("-5 + 3")` → `-2`
- A minus after an opening parenthesis must negate the sub-expression's first operand: `evaluate("(-3) * 2")` → `-6`
- Double negation must be handled: `evaluate("--5")` → `5`

### Test Quality

- Every new behavior listed above must have at least one dedicated test case that was written before the production code for that behavior
- Edge cases — empty string input, whitespace-only input, consecutive operators like `"2 ++ 3"`, and division-by-zero — must each have a test case asserting the correct exception type and message substring
- Test coverage for `src/python_starter/calculator.py` must be at least 90% line coverage as reported by `pytest --cov`

### Expected Functionality

- `evaluate("(2 + 3) * 4")` → `20`
- `evaluate("10 % 3")` → `1`
- `evaluate("-5 + 3")` → `-2`
- `evaluate("((1 + 2) * (3 + 4))")` → `21`
- `evaluate("5 % 0")` → raises `ValueError`
- `evaluate("(2 + )")` → raises `ValueError`
- `evaluate("")` → raises `ValueError`

## Acceptance Criteria

- All tests in `tests/test_calculator.py` pass when run with `make test`
- The test file contains at least 15 new test cases covering parentheses, modulo, unary negation, and their edge cases
- Line coverage of `src/python_starter/calculator.py` is at least 90%
- `make lint` and `make stylecheck` pass with no errors
- The `evaluate` function correctly handles all expression scenarios listed in the Requirements section
