# Task: Add a Packaging Demonstration Script to the Python Packaging Project

## Background

The packaging library (https://github.com/pypa/packaging) provides utilities for working with Python packages. A new demo script is needed that exercises the library's version parsing, specifier matching, and requirement handling capabilities, serving as both a usage example and a validation test.

## Files to Create

- `scripts/demo_packaging.py` — Demonstration script for packaging utilities

## Requirements

### Version Parsing

- Parse a variety of PEP 440 version strings (release, pre-release, post-release, dev, epoch-prefixed)
- Demonstrate version comparison and sorting
- Handle invalid version strings gracefully with informative error messages

### Specifier Matching

- Create version specifiers (e.g., `>=1.0,<2.0`, `~=1.4.2`, `!=1.5.0`) and test whether sample versions satisfy them
- Show how complex specifier sets combine multiple constraints

### Requirement Handling

- Parse requirement strings including extras and environment markers
- Display the parsed components (name, specifier, extras, marker)

### Output

- Print a structured report showing parsed results, comparison outcomes, and match verdicts
- The script must have a `__main__` entry point for direct execution

## Expected Functionality

- Running the script demonstrates correct parsing, comparison, and matching behavior
- Invalid inputs produce clear error messages rather than crashes
- Version ordering follows PEP 440 semantics

## Acceptance Criteria

- The demo script can parse and report on valid PEP 440 versions, including pre-release, post-release, dev, and epoch-based examples.
- Invalid version strings are reported cleanly without causing the script to crash.
- Specifier matching examples show correct inclusion and exclusion behavior for multiple version constraints.
- Requirement parsing output includes package name, specifier, extras, and environment marker details.
- The script presents results in a readable structure that demonstrates the `packaging` library's core capabilities.
