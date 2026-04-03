# Task: Implement a String Calculator Using Test-Driven Development

## Background

The python TDD starter repository (https://github.com/tdd-starters/python) provides a minimal Python project scaffold for practicing test-driven development. The task is to implement a `StringCalculator` class that parses and evaluates arithmetic expressions provided as strings, developed strictly through a red-green-refactor TDD cycle with comprehensive test coverage.

## Files to Create/Modify

- `src/string_calculator.py` (create) — `StringCalculator` class with an `add(numbers: str) -> int` method
- `tests/test_string_calculator.py` (create) — Full test suite covering unit, edge-case, and integration scenarios

## Requirements

### StringCalculator API

- The class exposes a single public method: `add(numbers: str) -> int`
- An empty string returns `0`
- A single number string (e.g., `"1"`) returns its integer value
- Two or more numbers separated by commas return their sum (e.g., `"1,2"` → `3`)
- Newlines between numbers are also valid delimiters (e.g., `"1\n2,3"` → `6`)
- A custom single-character delimiter can be specified on the first line with the format `//[delimiter]\n[numbers]` (e.g., `"//;\n1;2"` → `3`)
- Negative numbers raise a `ValueError` whose message includes all negative values found (e.g., `"1,-2,-3"` raises `ValueError: negative numbers not allowed: -2, -3`)
- Numbers greater than 1000 are ignored in the sum (e.g., `"2,1001"` → `2`)
- Custom delimiters may be of any length when enclosed in brackets: `//[***]\n1***2***3` → `6`
- Multiple custom delimiters can be specified: `//[*][%]\n1*2%3` → `6`

### Test Coverage

- Tests must be written before implementation code — the commit history or test structure should reflect a red-green-refactor progression
- Minimum 80% line coverage across `src/string_calculator.py`
- Tests must cover: empty input, single number, two numbers, multiple numbers, newline delimiters, custom delimiters, negative number rejection, numbers over 1000 ignored, multi-character delimiters, and multiple delimiters

### Edge Cases

- Input with trailing or leading whitespace around numbers (e.g., `" 1 , 2 "`) should be handled gracefully
- A delimiter line followed by an empty number section (e.g., `"//;\n"`) returns `0`
- Consecutive delimiters (e.g., `"1,,2"`) should raise a `ValueError` indicating invalid format

### Expected Functionality

- `add("")` → `0`
- `add("5")` → `5`
- `add("1,2,3")` → `6`
- `add("1\n2\n3")` → `6`
- `add("//;\n1;2;3")` → `6`
- `add("1,-2,3,-4")` → raises `ValueError: negative numbers not allowed: -2, -4`
- `add("2,1001")` → `2`
- `add("//[***]\n1***2***3")` → `6`
- `add("//[*][%]\n1*2%3")` → `6`
- `add("1,,2")` → raises `ValueError`

## Acceptance Criteria

- `StringCalculator.add()` returns correct results for all standard delimiter formats including comma, newline, single-character custom, multi-character custom, and multiple custom delimiters
- Negative numbers cause a `ValueError` that lists every negative value in the input
- Numbers greater than 1000 are excluded from the sum
- Invalid inputs (consecutive delimiters, malformed delimiter headers) raise appropriate errors
- Test suite achieves at least 80% line coverage over the implementation module
- All tests pass when run with `pytest`
