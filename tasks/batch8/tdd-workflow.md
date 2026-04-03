# Task: Implement a String Calculator Library Using Test-Driven Development

## Background

The Python TDD starter project (https://github.com/tdd-starters/python) provides a minimal Python package skeleton with `src/python_starter/` for source code and `tests/` for tests, configured with `pyproject.toml` and a `Makefile`. The task is to build a `StringCalculator` class that parses numeric strings with configurable delimiters and computes results, developed strictly test-first with comprehensive test coverage.

## Files to Create/Modify

- `src/python_starter/calculator.py` (create or modify) — `StringCalculator` class with an `add()` method and supporting logic
- `tests/test_calculator.py` (create or modify) — Comprehensive test suite covering all `StringCalculator` behaviors, edge cases, and error conditions

## Requirements

### Core `add()` Method

- `StringCalculator.add(numbers: str) -> int` takes a string of delimiter-separated numbers and returns their integer sum
- An empty string returns `0`
- A single number string (e.g., `"1"`) returns that number as an integer
- Two numbers separated by a comma (e.g., `"1,5"`) returns their sum (`6`)
- Any quantity of comma-separated numbers is supported (e.g., `"1,2,3,4,5"` returns `15`)

### Newline Delimiter Support

- Newline characters (`\n`) are valid delimiters in addition to commas
- `"1\n2,3"` returns `6`
- `"1,\n"` is invalid input — a delimiter must not appear immediately before or after another delimiter; this must raise a `ValueError`

### Custom Delimiter Declaration

- A custom single-character delimiter is declared via a header line in the format `"//[delimiter]\n[numbers]"`
- `"//;\n1;2"` returns `3` (semicolon is the delimiter)
- `"//|\n1|2|3"` returns `6`
- When a custom delimiter is declared, commas and newlines are no longer treated as delimiters unless the custom delimiter matches them

### Negative Number Handling

- Negative numbers must be rejected by raising a `ValueError`
- The exception message must contain the text `"negatives not allowed"` followed by a list of all negative numbers found (e.g., `"negatives not allowed: -1, -4"`)
- If multiple negative numbers are present, all must be listed in the exception message, not just the first one

### Large Number Handling

- Numbers greater than `1000` are ignored in the sum
- `"2,1001"` returns `2`
- `"1000,1001,6"` returns `1006` (1000 is included; 1001 is excluded)

### Multi-Character Custom Delimiters

- Custom delimiters of arbitrary length are declared as `"//[delimiter]\n[numbers]"`
- `"//[***]\n1***2***3"` returns `6`
- `"//[abc]\n1abc2abc3"` returns `6`

### Multiple Custom Delimiters

- Multiple custom delimiters are declared as `"//[delim1][delim2]\n[numbers]"`
- `"//[*][%]\n1*2%3"` returns `6`
- `"//[**][%%]\n1**2%%3"` returns `6`
- All declared delimiters must be recognized; the presence of unlisted separators between digits must be treated as part of the number (causing a `ValueError` if non-numeric)

### Test Coverage Requirements

- Tests must be written before the implementation code — the test file must contain at least 15 distinct test cases
- Test cases must cover: empty input, single number, two numbers, multiple numbers, newline delimiters, custom single-character delimiters, negative number rejection (single and multiple), numbers > 1000, multi-character delimiters, multiple delimiters simultaneously, and invalid formats
- Boundary values must be tested: `0`, `1000`, `1001`, empty string, string with only delimiters
- Overall branch coverage must be 80% or higher

## Expected Functionality

- `StringCalculator().add("")` → `0`
- `StringCalculator().add("1")` → `1`
- `StringCalculator().add("1,2,3,4")` → `10`
- `StringCalculator().add("1\n2\n3")` → `6`
- `StringCalculator().add("//;\n1;2;3")` → `6`
- `StringCalculator().add("-1,2,-3")` → raises `ValueError("negatives not allowed: -1, -3")`
- `StringCalculator().add("2,1001")` → `2`
- `StringCalculator().add("//[***]\n1***2***3")` → `6`
- `StringCalculator().add("//[*][%]\n1*2%3")` → `6`

## Acceptance Criteria

- `StringCalculator` class exists in `src/python_starter/calculator.py` with a public `add(numbers: str) -> int` method
- All test cases in `tests/test_calculator.py` pass when run with `pytest`
- At least 15 distinct test functions exist in the test file, covering every behavior listed in the Requirements
- Empty input returns `0`; single and multiple comma-separated numbers return correct sums
- Newline and custom delimiters are parsed and applied correctly
- Negative numbers raise `ValueError` with all negatives listed in the message
- Numbers exceeding 1000 are excluded from the sum
- Multi-character and multiple custom delimiters work correctly
- Test branch coverage is 80% or above as measured by `pytest --cov`
