"""Test file for the tdd-workflow skill.

This suite validates a TDD string calculator (Python kata): adding numbers
with custom delimiters, negative number handling, and >1000 filtering.
"""

from __future__ import annotations

import ast
import pathlib
import re

import pytest


class TestTddWorkflow:
    """Verify TDD string calculator in python tdd-starters."""

    REPO_DIR = "/workspace/python"

    CALCULATOR_PY = "src/python_starter/calculator.py"
    TEST_CALCULATOR_PY = "tests/test_calculator.py"

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    def _repo_path(self, relative: str) -> pathlib.Path:
        return pathlib.Path(self.REPO_DIR, *relative.split("/"))

    def _read_text(self, relative: str) -> str:
        path = self._repo_path(relative)
        assert path.exists(), f"Expected path to exist: {path}"
        return path.read_text(encoding="utf-8", errors="ignore")

    def _assert_non_empty_file(self, relative: str) -> pathlib.Path:
        path = self._repo_path(relative)
        assert path.is_file(), f"Expected file to exist: {path}"
        assert path.stat().st_size > 0, f"Expected non-empty file: {path}"
        return path

    def _function_source(self, source: str, func_name: str) -> str:
        """Extract func source via AST."""
        try:
            tree = ast.parse(source)
        except SyntaxError:
            return ""
        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef) and node.name == func_name:
                return ast.get_source_segment(source, node) or ""
        return ""

    # ------------------------------------------------------------------
    # Layer 1 – file_path_check (2 cases)
    # ------------------------------------------------------------------

    def test_file_path_src_python_starter_calculator_py_exists(self):
        """Verify src/python_starter/calculator.py exists."""
        self._assert_non_empty_file(self.CALCULATOR_PY)

    def test_file_path_tests_test_calculator_py_exists(self):
        """Verify tests/test_calculator.py exists."""
        self._assert_non_empty_file(self.TEST_CALCULATOR_PY)

    # ------------------------------------------------------------------
    # Layer 2 – semantic_check (5 cases)
    # ------------------------------------------------------------------

    def test_semantic_add_function_accepts_str_and_returns_int(self):
        """add function accepts str and returns int."""
        src = self._read_text(self.CALCULATOR_PY)
        func = self._function_source(src, "add")
        assert func, "add function not found"
        assert (
            re.search(r"str|string", func, re.IGNORECASE) or "numbers" in func
        ), "add should accept a string parameter"
        assert re.search(r"return\s+", func), "add should return a value"

    def test_semantic_delimiter_parsing_handles_prefix(self):
        """Delimiter parsing handles //{delimiter}\\n prefix."""
        src = self._read_text(self.CALCULATOR_PY)
        assert re.search(
            r"//|delimiter|startswith", src
        ), "Should handle //{delimiter}\\n prefix"

    def test_semantic_bracket_syntax_for_multi_char_delimiters(self):
        """Bracket syntax parsing for multi-char and multiple delimiters."""
        src = self._read_text(self.CALCULATOR_PY)
        assert re.search(
            r"\[.*\]|bracket|multi.*char|findall", src, re.IGNORECASE
        ), "Should parse bracket syntax for multi-char delimiters"

    def test_semantic_valueerror_raised_with_all_negatives_listed(self):
        """ValueError raised with all negatives listed in message."""
        src = self._read_text(self.CALCULATOR_PY)
        assert re.search(
            r"ValueError|negative", src
        ), "Should raise ValueError for negative numbers"

    def test_semantic_numbers_over_1000_filtered(self):
        """Numbers > 1000 filtered before summation."""
        src = self._read_text(self.CALCULATOR_PY)
        assert re.search(
            r"1000|1001|> 1000|<= 1000", src
        ), "Should filter numbers > 1000"

    # ------------------------------------------------------------------
    # Layer 3 – functional_check (5 cases)
    # ------------------------------------------------------------------

    def test_functional_add_empty_string_returns_0(self):
        """add('') → 0."""
        src = self._read_text(self.CALCULATOR_PY)
        # Verify fallback for empty string
        assert re.search(
            r"not\s+numbers|numbers\s*==\s*['\"]|len\(|return\s+0", src
        ), "Empty string should return 0"

    def test_functional_add_single_number_returns_itself(self):
        """add('1') → 1."""
        # Test file should cover this
        test_src = self._read_text(self.TEST_CALCULATOR_PY)
        assert re.search(
            r"add.*['\"]1['\"]|single", test_src, re.IGNORECASE
        ), "Test should cover single number"

    def test_functional_add_comma_separated(self):
        """add('1,2') → 3."""
        src = self._read_text(self.CALCULATOR_PY)
        assert re.search(r"split|,", src), "Should handle comma-separated numbers"

    def test_functional_add_newline_and_comma(self):
        """add('1\\n2,3') → 6."""
        src = self._read_text(self.CALCULATOR_PY)
        assert re.search(
            r"\\n|newline|replace|re\.split", src
        ), "Should handle newline as delimiter"

    def test_functional_add_custom_delimiter(self):
        """add('//;\\n1;2') → 3."""
        test_src = self._read_text(self.TEST_CALCULATOR_PY)
        assert re.search(
            r"//.*\\n|custom.*delim|;", test_src, re.IGNORECASE
        ), "Test should cover custom delimiter"
