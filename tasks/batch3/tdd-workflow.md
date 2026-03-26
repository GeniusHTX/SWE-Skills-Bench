# Task: Implement a String Calculator Using Test-Driven Development

## Background

The tdd-starters/python repository (https://github.com/tdd-starters/python) provides a minimal Python project skeleton for practicing test-driven development. The task is to implement a `StringCalculator` class that parses and evaluates numeric expressions from string inputs, with incrementally complex features that must be developed test-first.

## Files to Create/Modify

- `src/string_calculator.py` (create) — The `StringCalculator` class with an `add(numbers: str) -> int` method
- `tests/test_string_calculator.py` (create) — Comprehensive test suite driving the implementation

## Requirements

### Core Functionality

- `add("")` returns `0`
- `add("1")` returns `1`
- `add("1,2")` returns `3`
- `add` must handle any number of comma-separated values: `add("1,2,3,4,5")` returns `15`

### Newline Delimiter Support

- Newlines (`\n`) are valid delimiters in addition to commas: `add("1\n2,3")` returns `6`
- The input `"1,\n"` is invalid (trailing delimiter) and must raise `ValueError` with message `"Invalid input: trailing delimiter"`

### Custom Delimiters

- A custom single-character delimiter can be specified on the first line with format `//[delimiter]\n[numbers]`
- Example: `add("//;\n1;2")` returns `3`
- Example: `add("//|\n4|5|6")` returns `15`
- When a custom delimiter is specified, commas and newlines are no longer valid delimiters

### Custom Multi-Character Delimiters

- Multi-character delimiters are specified with square brackets: `//[***]\n1***2***3` returns `6`
- Multiple delimiters can be specified: `//[*][%]\n1*2%3` returns `6`
- Delimiter characters within brackets are treated literally (no regex interpretation)

### Negative Number Handling

- Negative numbers must raise `ValueError` with message `"Negatives not allowed: -1"` (listing the negative number)
- If multiple negatives are present, all must be listed: `"Negatives not allowed: -1, -3, -7"`

### Large Number Filtering

- Numbers greater than 1000 are ignored: `add("2,1001")` returns `2`
- Numbers exactly equal to 1000 are included: `add("1000,2")` returns `1002`

### Expected Functionality

- `add("")` → `0`
- `add("1,2,3")` → `6`
- `add("1\n2\n3")` → `6`
- `add("//;\n1;2;3")` → `6`
- `add("//[***]\n1***2***3")` → `6`
- `add("//[*][%]\n1*2%3")` → `6`
- `add("-1,2,-3")` → raises `ValueError("Negatives not allowed: -1, -3")`
- `add("2,1001,3")` → `5`
- `add("1,\n")` → raises `ValueError("Invalid input: trailing delimiter")`

## Acceptance Criteria

- The `StringCalculator.add` method handles empty strings, single numbers, and multiple comma-separated numbers correctly
- Newlines work as delimiters alongside commas in the default mode
- Custom single-character delimiters specified via `//[delim]\n` are recognized and applied
- Custom multi-character delimiters and multiple-delimiter specifications work correctly
- Negative numbers raise `ValueError` listing all negatives found in the input
- Numbers greater than 1000 are excluded from the sum; 1000 is included
- Invalid inputs (trailing delimiters) raise `ValueError` with a descriptive message
- Test coverage is at least 90% of the `StringCalculator` implementation
- Tests follow a clear progression from simple to complex scenarios
