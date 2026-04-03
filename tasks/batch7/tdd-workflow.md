# Task: Implement a String Calculator Using Test-Driven Development

## Background

The Python TDD Starter project (https://github.com/tdd-starters/python) provides a minimal skeleton for practicing test-driven development. The project contains `src/python_starter/` for source code and `tests/` for test files, with `tests/test_calculator.py` already scaffolded with one sample test and several commented-out test ideas. The task is to implement a fully functional string calculator following a strict test-first workflow with comprehensive coverage.

## Files to Create/Modify

- `src/python_starter/calculator.py` (create or modify) — String calculator implementation
- `tests/test_calculator.py` (modify) — Complete test suite covering all scenarios below

## Requirements

### String Calculator API

- Provide a function `add(numbers: str) -> int` that takes a string of delimited numbers and returns their sum
- An empty string returns `0`
- A single number (e.g., `"1"`) returns its integer value
- Two numbers separated by a comma (e.g., `"1,5"`) return their sum (`6`)
- An arbitrary count of numbers separated by commas is supported (e.g., `"1,2,3,4"` → `10`)

### Newline Delimiter Support

- Newline characters (`\n`) are accepted as an alternative delimiter alongside commas
- `"1\n2,3"` → `6`
- Mixing commas and newlines in the same input is valid

### Custom Delimiter Support

- A custom single-character delimiter may be declared in a header line of the form `//[delimiter]\n[numbers]`
- Example: `"//;\n1;2"` → `3`
- When a custom delimiter is declared, only that delimiter (not comma or newline) separates numbers in the body
- The delimiter character may be any non-digit, non-negative-sign character

### Negative Number Handling

- Calling `add` with a negative number raises a `ValueError`
- The exception message must include all negative numbers found in the input, not just the first one
- Example: `add("1,-2,-3")` raises `ValueError` with a message containing `-2` and `-3`

### Large Number Filtering

- Numbers greater than `1000` are ignored in the sum
- `"2,1001"` → `2`
- `"1000,1001,6"` → `1006` (1000 is included, 1001 is not)

### Multi-Character Custom Delimiter

- Custom delimiters of arbitrary length are supported using bracket syntax: `//[delimiter]\n[numbers]`
- Example: `"//[***]\n1***2***3"` → `6`
- Multiple distinct delimiters may be specified: `"//[*][%]\n1*2%3"` → `6`

### Test Coverage

- Every requirement above must be covered by at least one explicit test case
- Edge cases must be tested: empty string, single number, whitespace-only input, delimiter-only input, exactly-1000 value, exactly-1001 value
- Error cases must be tested: single negative, multiple negatives, negative with custom delimiter
- Test coverage across `calculator.py` must reach at least 80% line coverage

## Expected Functionality

- `add("")` → `0`
- `add("1")` → `1`
- `add("1,2")` → `3`
- `add("1\n2,3")` → `6`
- `add("//;\n1;2")` → `3`
- `add("1,-2,-3")` → raises `ValueError` with message containing both `-2` and `-3`
- `add("2,1001")` → `2`
- `add("//[***]\n1***2***3")` → `6`
- `add("//[*][%]\n1*2%3")` → `6`

## Acceptance Criteria

- The `add` function handles all delimiter forms (comma, newline, custom single-char, multi-char bracket, multiple bracket delimiters)
- Negative numbers cause a `ValueError` listing every negative number in the input
- Numbers above 1000 are excluded from the sum
- The test suite covers normal operation, all delimiter variants, negative-number errors, large-number filtering, and edge cases
- All tests pass via `make test` or `pytest`
- Test line coverage of the calculator module is at least 80%
