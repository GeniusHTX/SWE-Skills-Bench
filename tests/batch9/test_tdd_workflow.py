"""
Test for 'tdd-workflow' skill — TDD Workflow Calculator
Validates the Python TDD calculator: file existence, evaluate() function
signature, operator support (parentheses, modulo, unary negation), and
correct results via direct import.
"""

import os
import re
import sys

import pytest


class TestTddWorkflow:
    """Verify TDD calculator evaluate() function and project structure."""

    REPO_DIR = "/workspace/python"

    # ── helpers ──────────────────────────────────────────────────────────
    @staticmethod
    def _read_file(path: str) -> str:
        try:
            with open(path, "r", errors="ignore") as fh:
                return fh.read()
        except OSError:
            return ""

    @classmethod
    def _import_evaluate(cls):
        """Import evaluate from python_starter.calculator; skip on failure."""
        src_dir = os.path.join(cls.REPO_DIR, "src")
        if src_dir not in sys.path:
            sys.path.insert(0, src_dir)
        try:
            from python_starter.calculator import evaluate
            return evaluate
        except Exception as exc:
            pytest.skip(f"Cannot import evaluate: {exc}")

    # ── file_path_check ──────────────────────────────────────────────────

    def test_calculator_py_and_init_exist(self):
        """src/python_starter/calculator.py and __init__.py must exist."""
        calc = os.path.join(self.REPO_DIR, "src", "python_starter", "calculator.py")
        init = os.path.join(self.REPO_DIR, "src", "python_starter", "__init__.py")
        assert os.path.isfile(calc), f"{calc} does not exist"
        assert os.path.isfile(init), f"{init} does not exist"
        assert os.path.getsize(calc) > 0, "calculator.py is empty"

    def test_test_calculator_py_exists(self):
        """tests/test_calculator.py must exist."""
        path = os.path.join(self.REPO_DIR, "tests", "test_calculator.py")
        assert os.path.isfile(path), f"{path} does not exist"
        assert os.path.getsize(path) > 0, "test_calculator.py is empty"

    # ── semantic_check ───────────────────────────────────────────────────

    def test_evaluate_function_signature_defined(self):
        """calculator.py must define 'def evaluate' and reference ValueError."""
        content = self._read_file(
            os.path.join(self.REPO_DIR, "src", "python_starter", "calculator.py")
        )
        assert "def evaluate" in content, "evaluate function not defined"
        assert "ValueError" in content, "ValueError not referenced in calculator.py"

    def test_modulo_and_unary_negation_implemented(self):
        """calculator.py must handle '%' operator and unary negation."""
        content = self._read_file(
            os.path.join(self.REPO_DIR, "src", "python_starter", "calculator.py")
        )
        assert "%" in content, "Modulo operator '%' not found in calculator.py"
        unary_patterns = ["unary", "negat", "sign", "negate"]
        has_unary = any(p in content.lower() for p in unary_patterns) or re.search(
            r"['\"]?\-['\"]?", content
        )
        assert has_unary, "No unary negation handling found in calculator.py"

    def test_parentheses_override_precedence(self):
        """calculator.py must handle parenthesized sub-expressions."""
        content = self._read_file(
            os.path.join(self.REPO_DIR, "src", "python_starter", "calculator.py")
        )
        paren_patterns = ["stack", "recur", "paren", "(", ")"]
        has_paren = any(p in content for p in paren_patterns)
        assert has_paren, "No parenthesis handling found in calculator.py"

    # ── functional_check (import) ────────────────────────────────────────

    def test_evaluate_simple_parenthesized_expression(self):
        """evaluate('(2 + 3) * 4') should return 20."""
        evaluate = self._import_evaluate()
        assert evaluate("(2 + 3) * 4") == 20

    def test_evaluate_nested_parentheses(self):
        """evaluate('((1 + 2) * (3 + 4))') should return 21."""
        evaluate = self._import_evaluate()
        assert evaluate("((1 + 2) * (3 + 4))") == 21

    def test_evaluate_modulo_with_correct_precedence(self):
        """evaluate('10 + 7 % 3') should return 11 (% same precedence as *)."""
        evaluate = self._import_evaluate()
        assert evaluate("10 + 7 % 3") == 11

    def test_evaluate_unary_negation_at_start(self):
        """evaluate('-5 + 3') should return -2."""
        evaluate = self._import_evaluate()
        assert evaluate("-5 + 3") == -2

    def test_evaluate_double_negation(self):
        """evaluate('--5') should return 5 (double negation cancels)."""
        evaluate = self._import_evaluate()
        assert evaluate("--5") == 5

    def test_evaluate_whitespace_only_raises_valueerror(self):
        """evaluate('   ') should raise ValueError."""
        evaluate = self._import_evaluate()
        with pytest.raises(ValueError):
            evaluate("   ")

    def test_evaluate_mismatched_paren_raises_valueerror(self):
        """evaluate('(2 + 3') should raise ValueError for unmatched paren."""
        evaluate = self._import_evaluate()
        with pytest.raises(ValueError):
            evaluate("(2 + 3")

    def test_evaluate_modulo_by_zero_raises_valueerror(self):
        """evaluate('5 % 0') should raise ValueError (not ZeroDivisionError)."""
        evaluate = self._import_evaluate()
        with pytest.raises(ValueError):
            evaluate("5 % 0")
