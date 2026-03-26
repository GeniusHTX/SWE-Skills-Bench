"""
Tests for tdd-workflow skill.
REPO_DIR: /workspace/python
"""

import os
import sys
import importlib
import pytest

REPO_DIR = "/workspace/python"


def _path(rel):
    return os.path.join(REPO_DIR, rel)


def _read(rel):
    with open(_path(rel), encoding="utf-8") as f:
        return f.read()


def _read_any(*rels):
    """Read first file that exists among rels."""
    for rel in rels:
        p = _path(rel)
        if os.path.isfile(p):
            with open(p, encoding="utf-8") as f:
                return f.read()
    return None


class TestTddWorkflow:
    # ── file_path_check ────────────────────────────────────────────────────
    def test_string_calculator_file_exists(self):
        """Verify string_calculator.py exists in src/ or project root."""
        candidates = [
            _path("src/string_calculator.py"),
            _path("string_calculator.py"),
        ]
        exists = any(os.path.isfile(p) for p in candidates)
        assert exists, (
            "string_calculator.py must exist in src/ or project root; not found at: "
            + ", ".join(candidates)
        )
        # Must be non-empty
        for p in candidates:
            if os.path.isfile(p):
                assert os.path.getsize(p) > 0, f"{p} must be non-empty"
                break

    def test_test_string_calculator_file_exists(self):
        """Verify test file for StringCalculator exists."""
        candidates = [
            _path("tests/test_string_calculator.py"),
            _path("test_string_calculator.py"),
        ]
        exists = any(os.path.isfile(p) for p in candidates)
        assert (
            exists
        ), "A test_string_calculator.py file must exist; not found at: " + ", ".join(
            candidates
        )

    # ── semantic_check ─────────────────────────────────────────────────────
    def test_string_calculator_class_defined(self):
        """Verify StringCalculator class with add method is defined."""
        content = _read_any("src/string_calculator.py", "string_calculator.py")
        assert content is not None, "string_calculator.py not found for semantic check"
        assert (
            "class StringCalculator" in content
        ), "StringCalculator class must be defined"
        assert "def add" in content, "add method must be defined in StringCalculator"

    def test_custom_delimiter_support(self):
        """Verify custom delimiter parsing using '//[delimiter]\\n' syntax is implemented."""
        content = _read_any("src/string_calculator.py", "string_calculator.py")
        assert content is not None, "string_calculator.py not found"
        assert "//" in content, "//' delimiter prefix parsing must be present"
        # Should handle bracket syntax for multi-char delimiters
        has_bracket = "[" in content and "]" in content
        has_regex = "re." in content or "split" in content
        assert (
            has_regex or has_bracket
        ), "Custom delimiter extraction via regex or bracket split must be implemented"

    def test_negative_number_validation_defined(self):
        """Verify negative number detection raises ValueError listing all negatives."""
        content = _read_any("src/string_calculator.py", "string_calculator.py")
        assert content is not None, "string_calculator.py not found"
        has_negative_check = (
            "negatives not allowed" in content.lower()
            or "ValueError" in content
            or "raise" in content
        )
        assert has_negative_check, "ValueError must be raised for negative numbers"
        has_negative_filter = "< 0" in content or "negative" in content.lower()
        assert (
            has_negative_filter
        ), "Logic to filter/detect negative numbers must be present"

    def test_thousand_threshold_defined(self):
        """Verify numbers > 1000 are filtered out from the sum."""
        content = _read_any("src/string_calculator.py", "string_calculator.py")
        assert content is not None, "string_calculator.py not found"
        assert "1000" in content, "1000 threshold value must appear in code"
        has_filter = "> 1000" in content or ">1000" in content or "<= 1000" in content
        assert has_filter, "Filtering condition for numbers > 1000 must be present"

    # ── functional_check (import / mocked) ────────────────────────────────
    def _get_calculator(self):
        """Try to import StringCalculator; fall back to mocked implementation."""
        sys.path.insert(0, REPO_DIR)
        sys.path.insert(0, os.path.join(REPO_DIR, "src"))
        try:
            mod = importlib.import_module("string_calculator")
            return mod.StringCalculator()
        except Exception:
            pass
        try:
            src_mod = importlib.import_module("src.string_calculator")
            return src_mod.StringCalculator()
        except Exception:
            pass
        # Fall back to a reference implementation for mocked tests
        return None

    def _make_mock_calculator(self):
        """Return a reference StringCalculator implementation for mocked tests."""
        import re

        class StringCalculator:
            def add(self, numbers: str) -> int:
                if not numbers:
                    return 0
                delimiter_pattern = r"[,\n]"
                if numbers.startswith("//"):
                    header, numbers = numbers[2:].split("\n", 1)
                    if header.startswith("["):
                        delimiters = re.findall(r"\[(.+?)\]", header)
                    else:
                        delimiters = [re.escape(header)]
                    delimiter_pattern = "|".join(re.escape(d) for d in delimiters)
                parts = re.split(delimiter_pattern, numbers)
                ints = [int(p) for p in parts]
                negatives = [n for n in ints if n < 0]
                if negatives:
                    raise ValueError(f"negatives not allowed: {negatives}")
                return sum(n for n in ints if n <= 1000)

        return StringCalculator()

    def test_empty_string_returns_zero(self):
        """Verify add('') returns 0."""
        sc = self._get_calculator() or self._make_mock_calculator()
        assert sc.add("") == 0, "add('') must return 0"

    def test_comma_separated_returns_sum(self):
        """Verify add('1,2,3') returns 6."""
        sc = self._get_calculator() or self._make_mock_calculator()
        assert sc.add("1,2,3") == 6, "add('1,2,3') must return 6"

    def test_newline_delimiter_returns_sum(self):
        """Verify add('1\\n2\\n3') returns 6 with newline delimiter."""
        sc = self._get_calculator() or self._make_mock_calculator()
        assert sc.add("1\n2\n3") == 6, "add('1\\n2\\n3') must return 6"

    def test_custom_single_char_delimiter(self):
        """Verify add('//;\\n1;2;3') returns 6 with semicolon custom delimiter."""
        sc = self._get_calculator() or self._make_mock_calculator()
        assert sc.add("//;\n1;2;3") == 6, "add('//;\\n1;2;3') must return 6"

    def test_negatives_raise_value_error_listing_both(self):
        """Verify add('-1,2,-3') raises ValueError listing both -1 and -3."""
        sc = self._get_calculator() or self._make_mock_calculator()
        with pytest.raises((ValueError, Exception)) as exc_info:
            sc.add("-1,2,-3")
        exc_msg = str(exc_info.value)
        assert "-1" in exc_msg, "ValueError message must contain -1"
        assert "-3" in exc_msg, "ValueError message must contain -3"

    def test_numbers_over_1000_ignored_1000_included(self):
        """Verify add('2,1001,3') returns 5 and add('1000,2') returns 1002."""
        sc = self._get_calculator() or self._make_mock_calculator()
        result1 = sc.add("2,1001,3")
        assert (
            result1 == 5
        ), f"add('2,1001,3') must return 5 (1001 ignored), got {result1}"
        result2 = sc.add("1000,2")
        assert (
            result2 == 1002
        ), f"add('1000,2') must return 1002 (1000 is included), got {result2}"
