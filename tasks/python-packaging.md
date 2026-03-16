# Task: Add Version Parsing Edge Case Tests for Python Packaging

## Background
   Add integration tests covering version number parsing edge cases
   and a demo script showing packaging library usage.

## Files to Create/Modify
   - tests/test_version_edge_cases.py (new tests)
   - scripts/demo_packaging.py (new demo script)

## Requirements
   
   Edge Cases to Test:
   - Pre-release versions: 1.0a1, 1.0b2, 1.0rc1
   - Local version identifiers: 1.0+local, 1.0+ubuntu1
   - Epoch versions: 1!2.0
   - Post-release: 1.0.post1
   - Dev versions: 1.0.dev1
   
   Demo Script Features:
   - Version comparison examples
   - Specifier filtering demonstration
   - Wheel metadata parsing
   - Complete usage workflow

4. Test Coverage:
   - Version parsing correctness
   - Specifier matching logic
   - Version comparison operators
   - Error handling for invalid versions

## Acceptance Criteria

   - `python scripts/demo_packaging.py` outputs comparison results
   - All edge case versions parsed correctly
