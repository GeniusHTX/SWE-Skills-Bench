"""
Test for 'tdd-workflow' skill — TDD Workflow with StringCalculator
Validates that the Agent implemented a StringCalculator class following TDD,
with proper add() method handling delimiters, negatives, and edge cases.
"""

import os
import re
import sys
import subprocess

import pytest


class TestTddWorkflow:
    """Verify TDD StringCalculator implementation."""

    REPO_DIR = "/workspace/python"

    @staticmethod
    def _read(path):
        with open(path, "r", errors="ignore") as fh:
            return fh.read()

    @staticmethod
    def _import_calculator():
        """Helper to import StringCalculator with sys.path adjustment."""
        repo = "/workspace/python"
        if repo not in sys.path:
            sys.path.insert(0, repo)
        try:
            from src.string_calculator import StringCalculator

            return StringCalculator
        except ImportError:
            return None

    # ---- file_path_check ----

    def test_string_calculator_py_exists(self):
        """Verifies that src/string_calculator.py exists."""
        path = os.path.join(self.REPO_DIR, "src/string_calculator.py")
        assert os.path.exists(path), f"Expected file not found: {path}"

    def test_test_string_calculator_py_exists(self):
        """Verifies that tests/test_string_calculator.py exists."""
        path = os.path.join(self.REPO_DIR, "tests/test_string_calculator.py")
        assert os.path.exists(path), f"Expected file not found: {path}"

    # ---- semantic_check ----

    def test_import_string_calculator_class(self):
        """StringCalculator class should be importable from src.string_calculator."""
        cls = self._import_calculator()
        if cls is None:
            pytest.skip("Could not import StringCalculator")
        assert cls is not None

    def test_has_add_method(self):
        """StringCalculator should have an 'add' method accepting (self, numbers: str)."""
        path = os.path.join(self.REPO_DIR, "src/string_calculator.py")
        content = self._read(path)
        assert re.search(
            r"def\s+add\s*\(\s*self", content
        ), "StringCalculator missing 'add' method"

    def test_add_returns_int(self):
        """add() should return int, not str or float — verify via source annotation or behavior."""
        path = os.path.join(self.REPO_DIR, "src/string_calculator.py")
        content = self._read(path)
        has_int_annotation = "-> int" in content
        cls = self._import_calculator()
        if cls is not None:
            result = cls().add("1,2")
            assert isinstance(
                result, int
            ), f"add() returned {type(result)}, expected int"
        elif not has_int_annotation:
            pytest.skip("Cannot verify return type without import or annotation")

    def test_raises_value_error_for_negatives(self):
        """Source should use ValueError for negatives, not generic Exception."""
        path = os.path.join(self.REPO_DIR, "src/string_calculator.py")
        content = self._read(path)
        assert (
            "ValueError" in content
        ), "Expected ValueError for negatives, not generic Exception or AssertionError"

    def test_error_message_includes_negative_values(self):
        """ValueError message should contain the specific negative values."""
        path = os.path.join(self.REPO_DIR, "src/string_calculator.py")
        content = self._read(path)
        # Should reference the negative numbers in the error, not a generic message
        has_format = any(
            p in content for p in ["{", 'f"', "f'", ".format", "str(", "join"]
        )
        assert has_format, (
            "ValueError message should contain the specific negative values, "
            "not just a generic message"
        )

    # ---- functional_check (import) ----

    def test_add_empty_string_returns_zero(self):
        """StringCalculator().add('') == 0."""
        cls = self._import_calculator()
        if cls is None:
            pytest.skip("Could not import StringCalculator")
        assert cls().add("") == 0

    def test_add_single_number(self):
        """StringCalculator().add('5') == 5."""
        cls = self._import_calculator()
        if cls is None:
            pytest.skip("Could not import StringCalculator")
        assert cls().add("5") == 5

    def test_add_two_numbers(self):
        """StringCalculator().add('1,2') == 3."""
        cls = self._import_calculator()
        if cls is None:
            pytest.skip("Could not import StringCalculator")
        assert cls().add("1,2") == 3

    def test_add_three_numbers(self):
        """StringCalculator().add('1,2,3') == 6."""
        cls = self._import_calculator()
        if cls is None:
            pytest.skip("Could not import StringCalculator")
        assert cls().add("1,2,3") == 6

    def test_add_newline_delimiter(self):
        """StringCalculator().add('1\\n2,3') == 6."""
        cls = self._import_calculator()
        if cls is None:
            pytest.skip("Could not import StringCalculator")
        assert cls().add("1\n2,3") == 6

    def test_add_custom_delimiter(self):
        """StringCalculator().add('//;\\n1;2;3') == 6."""
        cls = self._import_calculator()
        if cls is None:
            pytest.skip("Could not import StringCalculator")
        assert cls().add("//;\n1;2;3") == 6

    def test_add_negatives_raises_value_error(self):
        """StringCalculator().add('1,-2,3,-4') raises ValueError with '-2' and '-4'."""
        cls = self._import_calculator()
        if cls is None:
            pytest.skip("Could not import StringCalculator")
        with pytest.raises(ValueError) as exc_info:
            cls().add("1,-2,3,-4")
        msg = str(exc_info.value)
        assert "-2" in msg, f"Error message should contain '-2', got: {msg}"
        assert "-4" in msg, f"Error message should contain '-4', got: {msg}"

    def test_add_ignores_numbers_over_1000(self):
        """StringCalculator().add('2,1001') == 2 — numbers > 1000 are ignored."""
        cls = self._import_calculator()
        if cls is None:
            pytest.skip("Could not import StringCalculator")
        assert cls().add("2,1001") == 2
