"""
Test for 'python-anti-patterns' skill — Python Anti-Pattern Review
Validates that the Agent refactored boltons/iterutils.py and boltons/strutils.py
to use modern Python 3.9+ patterns while keeping all existing tests passing.
"""

import os
import re
import ast
import subprocess
import pytest


class TestPythonAntiPatterns:
    """Verify modernisation of boltons core modules."""

    REPO_DIR = "/workspace/boltons"

    # ------------------------------------------------------------------
    # L1: file & syntax
    # ------------------------------------------------------------------

    def test_iterutils_exists(self):
        """boltons/iterutils.py must exist."""
        assert os.path.isfile(os.path.join(self.REPO_DIR, "boltons", "iterutils.py"))

    def test_strutils_exists(self):
        """boltons/strutils.py must exist."""
        assert os.path.isfile(os.path.join(self.REPO_DIR, "boltons", "strutils.py"))

    def test_iterutils_compiles(self):
        """iterutils.py must compile without syntax errors."""
        result = subprocess.run(
            ["python", "-m", "py_compile", "boltons/iterutils.py"],
            cwd=self.REPO_DIR,
            capture_output=True,
            text=True,
            timeout=30,
        )
        assert result.returncode == 0, f"Syntax error:\n{result.stderr}"

    def test_strutils_compiles(self):
        """strutils.py must compile without syntax errors."""
        result = subprocess.run(
            ["python", "-m", "py_compile", "boltons/strutils.py"],
            cwd=self.REPO_DIR,
            capture_output=True,
            text=True,
            timeout=30,
        )
        assert result.returncode == 0, f"Syntax error:\n{result.stderr}"

    # ------------------------------------------------------------------
    # L2: pattern modernisation checks
    # ------------------------------------------------------------------

    def _read(self, relpath):
        fpath = os.path.join(self.REPO_DIR, relpath)
        with open(fpath, "r", encoding="utf-8") as f:
            return f.read()

    def test_iterutils_uses_fstrings(self):
        """iterutils.py should use f-strings instead of .format()."""
        src = self._read("boltons/iterutils.py")
        tree = ast.parse(src)
        fstring_count = sum(1 for n in ast.walk(tree) if isinstance(n, ast.JoinedStr))
        assert (
            fstring_count >= 1
        ), "No f-strings found in iterutils.py — expected modernisation"

    def test_strutils_uses_fstrings(self):
        """strutils.py should use f-strings instead of .format()."""
        src = self._read("boltons/strutils.py")
        tree = ast.parse(src)
        fstring_count = sum(1 for n in ast.walk(tree) if isinstance(n, ast.JoinedStr))
        assert (
            fstring_count >= 1
        ), "No f-strings found in strutils.py — expected modernisation"

    def test_no_type_eq_checks_iterutils(self):
        """iterutils.py should not use type(x) == ... comparisons."""
        src = self._read("boltons/iterutils.py")
        matches = re.findall(r"\btype\s*\([^)]+\)\s*==", src)
        assert (
            len(matches) == 0
        ), f"Found type(x)==... patterns in iterutils.py: {matches[:5]}"

    def test_no_type_eq_checks_strutils(self):
        """strutils.py should not use type(x) == ... comparisons."""
        src = self._read("boltons/strutils.py")
        matches = re.findall(r"\btype\s*\([^)]+\)\s*==", src)
        assert (
            len(matches) == 0
        ), f"Found type(x)==... patterns in strutils.py: {matches[:5]}"

    def test_no_bare_except_strutils(self):
        """strutils.py should not use bare except: clauses."""
        src = self._read("boltons/strutils.py")
        tree = ast.parse(src)
        for node in ast.walk(tree):
            if isinstance(node, ast.ExceptHandler):
                # bare except has type=None
                assert (
                    node.type is not None
                ), f"Bare except: found at line {node.lineno} in strutils.py"

    def test_existing_tests_pass(self):
        """All existing boltons tests must continue to pass."""
        result = subprocess.run(
            ["python", "-m", "pytest", "tests/", "-x", "-q", "--tb=short"],
            cwd=self.REPO_DIR,
            capture_output=True,
            text=True,
            timeout=300,
        )
        assert (
            result.returncode == 0
        ), f"Existing tests failed (rc={result.returncode}):\n{result.stdout[-2000:]}\n{result.stderr[-1000:]}"
