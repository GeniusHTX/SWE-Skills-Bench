# Task: Implement a String Calculator Using Test-Driven Development

## Background

The TDD starters repository (https://github.com/tdd-starters/python) provides a minimal Python project structure for practicing Test-Driven Development. This task requires implementing a `StringCalculator` class following strict TDD methodology: write a failing test first, then write the minimum code to make it pass, then refactor. The calculator parses a string of numbers with configurable delimiters and returns the sum.

## Files to Create/Modify

- `src/string_calculator.py` (create) — `StringCalculator` class with an `add(numbers: str) -> int` method that parses a string of delimited numbers and returns their sum.
- `tests/test_string_calculator.py` (create) — Test suite with at least 10 test cases, written in TDD progression order, covering each incremental feature.

## Requirements

### Feature 1: Empty String

- `add("")` → returns `0`.

### Feature 2: Single Number

- `add("1")` → returns `1`.
- `add("42")` → returns `42`.

### Feature 3: Two Numbers (Comma-Delimited)

- `add("1,2")` → returns `3`.

### Feature 4: Multiple Numbers

- `add("1,2,3,4,5")` → returns `15`.
- Support any count of numbers.

### Feature 5: Newline Delimiter

- `add("1\n2,3")` → returns `6`.
- Newlines and commas are both valid delimiters.

### Feature 6: Custom Delimiter

- Format: `"//[delimiter]\n[numbers]"`.
- `add("//;\n1;2;3")` → returns `6` (semicolon delimiter).
- `add("//|\n4|5|6")` → returns `15` (pipe delimiter).

### Feature 7: Negative Numbers

- `add("1,-2,3,-4")` → raises `ValueError` with message `"negatives not allowed: -2, -4"`.
- The error message must list ALL negative numbers, not just the first.

### Feature 8: Numbers Greater Than 1000

- Numbers greater than 1000 are ignored.
- `add("2,1001")` → returns `2`.
- `add("1000,1001,999")` → returns `1999` (1000 is included, 1001 is ignored).

### Feature 9: Multi-Character Custom Delimiter

- Format: `"//[***]\n1***2***3"` (delimiter enclosed in brackets).
- `add("//[***]\n1***2***3")` → returns `6`.

### Feature 10: Multiple Custom Delimiters

- Format: `"//[delim1][delim2]\n..."`.
- `add("//[*][%]\n1*2%3")` → returns `6`.
- `add("//[**][%%]\n1**2%%3")` → returns `6`.

### TDD Discipline

- Tests must be written in order matching the feature progression above.
- Each test should fail before its corresponding implementation is added.
- Name tests clearly: `test_empty_string_returns_zero`, `test_single_number`, `test_two_numbers_comma_delimited`, etc.
- There should be exactly one `StringCalculator` class with one public method `add`.

### Expected Functionality

- `StringCalculator().add("")` → `0`
- `StringCalculator().add("1,2,3")` → `6`
- `StringCalculator().add("//[***][%%]\n1***2%%3")` → `6`
- `StringCalculator().add("1,-2")` → `ValueError: negatives not allowed: -2`
- `StringCalculator().add("2,1001")` → `2`

## Acceptance Criteria

- `StringCalculator` class is implemented in `src/string_calculator.py` with the `add(numbers: str) -> int` method.
- All 10 features are supported and tested.
- Negative numbers raise `ValueError` listing all negatives.
- Numbers > 1000 are ignored.
- Custom single-char, multi-char, and multiple delimiters work correctly.
- At least 10 test cases exist covering each feature, plus edge cases (whitespace, consecutive delimiters).
- All tests pass with `pytest tests/test_string_calculator.py -v`.
