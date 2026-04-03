# Task: Implement a Password Strength Validator Using Test-Driven Development

## Background

The `tdd-starters/python` repository is a minimal Python project scaffold configured with pytest and coverage tooling. A `PasswordValidator` class needs to be added to the `src/python_starter/` package that evaluates password strength and returns structured feedback. All production code must be written only after corresponding test cases exist and fail, following the red-green-refactor cycle. The final test suite must achieve at least 80% line coverage.

## Files to Create/Modify

- `src/python_starter/password_validator.py` (create) — `PasswordValidator` class with `validate(password: str)` method
- `tests/test_password_validator.py` (create) — Complete test suite covering all validation rules, edge cases, and error conditions
- `pyproject.toml` (modify) — Add coverage threshold configuration if not already present

## Requirements

### PasswordValidator Class

- Expose a single public method: `validate(password: str) -> dict`
- The returned dict must contain:
  - `"valid"`: `bool` — `True` only when every rule passes
  - `"score"`: `int` — integer 0–5 representing how many of the five strength rules pass
  - `"errors"`: `list[str]` — one human-readable message per failed rule, empty list when all pass

### Validation Rules

The five strength rules, evaluated independently:

1. **Length** — password must be at least 8 characters
2. **Uppercase** — password must contain at least one uppercase letter (`A-Z`)
3. **Lowercase** — password must contain at least one lowercase letter (`a-z`)
4. **Digit** — password must contain at least one digit (`0-9`)
5. **Special character** — password must contain at least one character from the set `!@#$%^&*()-_=+[]{}|;:'",.<>?/`

### Error Messages

Each failed rule must produce exactly one of these messages in `"errors"`:

- `"Password must be at least 8 characters"`
- `"Password must contain at least one uppercase letter"`
- `"Password must contain at least one lowercase letter"`
- `"Password must contain at least one digit"`
- `"Password must contain at least one special character"`

### Input Edge Cases

- `validate("")` → `{"valid": False, "score": 0, "errors": [all five messages]}`
- `validate(None)` → raises `TypeError`
- `validate(12345)` → raises `TypeError`
- Whitespace-only strings (e.g., `"        "`) count toward length but do not satisfy uppercase, lowercase, digit, or special character rules
- Unicode letters (e.g., `"Ü"`, `"ñ"`) do not satisfy the uppercase or lowercase rules — only ASCII `A-Z` / `a-z` count

### Test Suite Structure

- Tests must be placed in `tests/test_password_validator.py`
- Tests must import from `src.python_starter.password_validator`
- The test file must be runnable via `make test` or `python -m pytest tests/`
- Tests must include:
  - A case for a fully valid password (score 5, no errors)
  - A case for an empty string (score 0, all errors)
  - One case per individual rule failure (password satisfies all rules except the one under test)
  - Cases for `None` and non-string input raising `TypeError`
  - A case for a whitespace-only string of length ≥ 8
  - A case verifying the exact error message strings

### Coverage

- Line coverage across `src/python_starter/password_validator.py` must be ≥ 80%
- Coverage can be measured with `python -m pytest --cov=src/python_starter --cov-report=term-missing tests/`

### Expected Functionality

- `validate("Str0ng!Pass")` → `{"valid": True, "score": 5, "errors": []}`
- `validate("short")` → `{"valid": False, "score": 1, "errors": [length, uppercase, digit, special messages]}`
- `validate("ALLUPPERCASE1!")` → `{"valid": False, "score": 4, "errors": ["Password must contain at least one lowercase letter"]}`
- `validate("abcdefgh")` → `{"valid": False, "score": 2, "errors": [uppercase, digit, special messages]}`
- `validate("")` → `{"valid": False, "score": 0, "errors": [all five messages]}`
- `validate(None)` → `TypeError` raised

## Acceptance Criteria

- `python -m pytest tests/test_password_validator.py -v` exits with all tests passing
- Tests exist and fail before the corresponding production code is written (red-green cycle)
- `PasswordValidator.validate` returns the correct `valid`, `score`, and `errors` for every rule combination
- Invalid inputs (`None`, non-string) raise `TypeError`
- Line coverage of `src/python_starter/password_validator.py` is ≥ 80%
- No test depends on the execution order or mutable shared state of another test
