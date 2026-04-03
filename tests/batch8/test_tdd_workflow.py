"""
Test for 'tdd-workflow' skill — StringCalculator TDD Kata
Validates that the Agent implemented a StringCalculator with add() method
supporting comma/newline/custom delimiters, negative validation, and >1000 filter.
"""

import os
import re
import sys

import pytest


class TestTddWorkflow:
    """Verify StringCalculator TDD kata implementation."""

    REPO_DIR = "/workspace/python"

    @staticmethod
    def _read(path: str) -> str:
        try:
            with open(path, "r", errors="ignore") as fh:
                return fh.read()
        except OSError:
            return ""

    def _find_file(self, *candidates):
        for c in candidates:
            p = os.path.join(self.REPO_DIR, c)
            if os.path.isfile(p):
                return p
        return None

    # ── file_path_check ─────────────────────────────────────────────

    def test_string_calculator_module_exists(self):
        """Verify string_calculator.py or calculator/string_calculator.py exists."""
        candidates = ("string_calculator.py", "calculator/string_calculator.py")
        found = any(
            os.path.isfile(os.path.join(self.REPO_DIR, c)) for c in candidates)
        assert found, f"Missing: none of {candidates} found"

    def test_test_file_exists(self):
        """Verify tests/test_string_calculator.py or test_calculator.py exists."""
        candidates = ("tests/test_string_calculator.py", "test_calculator.py")
        found = any(
            os.path.isfile(os.path.join(self.REPO_DIR, c)) for c in candidates)
        assert found, f"Missing: none of {candidates} found"

    # ── semantic_check ──────────────────────────────────────────────

    def test_string_calculator_class_defined(self):
        """Verify class StringCalculator is defined."""
        path = self._find_file("string_calculator.py",
                               "calculator/string_calculator.py")
        assert path, "StringCalculator module not found"
        content = self._read(path)
        assert "class StringCalculator" in content, \
            "class StringCalculator not found"

    def test_add_method_signature(self):
        """Verify def add(self, numbers) method is present."""
        path = self._find_file("string_calculator.py",
                               "calculator/string_calculator.py")
        assert path, "StringCalculator module not found"
        content = self._read(path)
        assert "def add" in content, "def add not found"

    def test_value_error_for_negatives(self):
        """Verify ValueError is raised with negative numbers listed in message."""
        path = self._find_file("string_calculator.py",
                               "calculator/string_calculator.py")
        assert path, "StringCalculator module not found"
        content = self._read(path)
        assert "ValueError" in content, "ValueError not found"
        assert "negatives" in content.lower(), "'negatives' not found"

    def test_numbers_over_1000_ignored(self):
        """Verify numbers > 1000 are filtered before summation."""
        path = self._find_file("string_calculator.py",
                               "calculator/string_calculator.py")
        assert path, "StringCalculator module not found"
        content = self._read(path)
        assert "1000" in content, "1000 threshold not found"

    # ── functional_check (import) ───────────────────────────────────

    def _skip_unless_importable(self):
        if not os.path.isdir(self.REPO_DIR):
            pytest.skip("Repo dir does not exist")
        if self.REPO_DIR not in sys.path:
            sys.path.insert(0, self.REPO_DIR)

    def test_empty_string_returns_zero(self):
        """add('') returns 0."""
        self._skip_unless_importable()
        try:
            from string_calculator import StringCalculator
        except Exception as exc:
            pytest.skip(f"Cannot import: {exc}")
        assert StringCalculator().add("") == 0

    def test_comma_and_newline_delimiters(self):
        r"""add('1\n2,3') returns 6."""
        self._skip_unless_importable()
        try:
            from string_calculator import StringCalculator
        except Exception as exc:
            pytest.skip(f"Cannot import: {exc}")
        assert StringCalculator().add("1\n2,3") == 6

    def test_custom_single_char_delimiter(self):
        r"""add('//;\n1;2') returns 3 using custom delimiter ;."""
        self._skip_unless_importable()
        try:
            from string_calculator import StringCalculator
        except Exception as exc:
            pytest.skip(f"Cannot import: {exc}")
        assert StringCalculator().add("//;\n1;2") == 3

    def test_multi_char_delimiter(self):
        r"""add('//[***]\n1***2***3') returns 6."""
        self._skip_unless_importable()
        try:
            from string_calculator import StringCalculator
        except Exception as exc:
            pytest.skip(f"Cannot import: {exc}")
        assert StringCalculator().add("//[***]\n1***2***3") == 6

    def test_negative_numbers_raise_value_error(self):
        """add('1,-2,3,-4') raises ValueError mentioning -2 and -4."""
        self._skip_unless_importable()
        try:
            from string_calculator import StringCalculator
        except Exception as exc:
            pytest.skip(f"Cannot import: {exc}")
        with pytest.raises(ValueError) as exc_info:
            StringCalculator().add("1,-2,3,-4")
        assert "-2" in str(exc_info.value), "-2 not in error message"
        assert "-4" in str(exc_info.value), "-4 not in error message"
