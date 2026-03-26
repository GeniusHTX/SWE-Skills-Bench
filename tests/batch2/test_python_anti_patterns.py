"""
Test for 'python-anti-patterns' skill — Python Anti-Pattern Review
Validates that the Agent refactored anti-patterns in boltons iterutils.py and
strutils.py — replacing manual type checks, bare excepts, old-style formatting —
while preserving all existing functionality.
"""

import os
import re
import subprocess

import pytest

from _dependency_utils import ensure_python_dependencies


@pytest.fixture(scope="module", autouse=True)
def _ensure_repo_dependencies():
    ensure_python_dependencies(TestPythonAntiPatterns.REPO_DIR)


class TestPythonAntiPatterns:
    """Verify anti-pattern refactoring in boltons iterutils and strutils."""

    REPO_DIR = "/workspace/boltons"

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    def _read(self, *parts):
        fpath = os.path.join(self.REPO_DIR, *parts)
        assert os.path.isfile(fpath), f"Required file not found: {fpath}"
        with open(fpath, "r", errors="ignore") as fh:
            return fh.read()

    # ------------------------------------------------------------------
    # L1: Files exist and compile
    # ------------------------------------------------------------------

    def test_iterutils_compiles(self):
        """boltons/iterutils.py must be syntactically valid Python."""
        result = subprocess.run(
            ["python", "-m", "py_compile", "boltons/iterutils.py"],
            cwd=self.REPO_DIR,
            capture_output=True,
            text=True,
            timeout=30,
        )
        assert result.returncode == 0, f"Syntax error in iterutils.py:\n{result.stderr}"

    def test_strutils_compiles(self):
        """boltons/strutils.py must be syntactically valid Python."""
        result = subprocess.run(
            ["python", "-m", "py_compile", "boltons/strutils.py"],
            cwd=self.REPO_DIR,
            capture_output=True,
            text=True,
            timeout=30,
        )
        assert result.returncode == 0, f"Syntax error in strutils.py:\n{result.stderr}"

    # ------------------------------------------------------------------
    # L2: No type(x) == ... anti-pattern
    # ------------------------------------------------------------------

    def test_iterutils_no_manual_type_equality(self):
        """iterutils.py must not use type(x) == ... or type(x) is ... for type checking."""
        content = self._read("boltons", "iterutils.py")
        # Match: type(something) == SomeType or type(something) is SomeType
        bad_patterns = re.findall(
            r"type\s*\([^)]+\)\s*(?:==|is)\s*(?!None)\w+", content
        )
        assert len(bad_patterns) == 0, (
            f"iterutils.py still contains {len(bad_patterns)} manual type equality check(s): "
            f"{bad_patterns[:5]}"
        )

    def test_strutils_no_manual_type_equality(self):
        """strutils.py must not use type(x) == ... or type(x) is ... for type checking."""
        content = self._read("boltons", "strutils.py")
        bad_patterns = re.findall(
            r"type\s*\([^)]+\)\s*(?:==|is)\s*(?!None)\w+", content
        )
        assert len(bad_patterns) == 0, (
            f"strutils.py still contains {len(bad_patterns)} manual type equality check(s): "
            f"{bad_patterns[:5]}"
        )

    # ------------------------------------------------------------------
    # L2: No bare except clauses
    # ------------------------------------------------------------------

    def test_iterutils_no_bare_except(self):
        """iterutils.py must not contain bare 'except:' clauses."""
        content = self._read("boltons", "iterutils.py")
        # Match bare except (not except Something or except (A, B))
        bare_excepts = re.findall(r"^\s*except\s*:", content, re.MULTILINE)
        assert (
            len(bare_excepts) == 0
        ), f"iterutils.py still contains {len(bare_excepts)} bare except clause(s)"

    def test_strutils_no_bare_except(self):
        """strutils.py must not contain bare 'except:' clauses."""
        content = self._read("boltons", "strutils.py")
        bare_excepts = re.findall(r"^\s*except\s*:", content, re.MULTILINE)
        assert (
            len(bare_excepts) == 0
        ), f"strutils.py still contains {len(bare_excepts)} bare except clause(s)"

    # ------------------------------------------------------------------
    # L2: Modern string formatting (f-strings where appropriate)
    # ------------------------------------------------------------------

    def test_iterutils_reduces_old_style_formatting(self):
        """iterutils.py should prefer f-strings over % formatting or .format() where readable."""
        content = self._read("boltons", "iterutils.py")
        # Count old-style patterns
        percent_fmt = len(re.findall(r'["\'].*%[sd].*["\']\s*%', content))
        format_calls = len(re.findall(r"\.format\s*\(", content))
        fstrings = len(re.findall(r'f["\']', content))
        total_old = percent_fmt + format_calls
        # We don't require zero old-style, but if there are many old-style and
        # zero f-strings, the refactoring likely wasn't done
        if total_old > 3:
            assert fstrings >= 1, (
                f"iterutils.py has {total_old} old-style format expressions but "
                f"no f-strings — refactoring to modern formatting appears incomplete"
            )

    def test_strutils_reduces_old_style_formatting(self):
        """strutils.py should prefer f-strings over % formatting or .format() where readable."""
        content = self._read("boltons", "strutils.py")
        percent_fmt = len(re.findall(r'["\'].*%[sd].*["\']\s*%', content))
        format_calls = len(re.findall(r"\.format\s*\(", content))
        fstrings = len(re.findall(r'f["\']', content))
        total_old = percent_fmt + format_calls
        if total_old > 3:
            assert fstrings >= 1, (
                f"strutils.py has {total_old} old-style format expressions but "
                f"no f-strings — refactoring to modern formatting appears incomplete"
            )

    # ------------------------------------------------------------------
    # L2: isinstance usage
    # ------------------------------------------------------------------

    def test_isinstance_used_for_type_checks(self):
        """Refactored code should use isinstance() for type checking."""
        content_iter = self._read("boltons", "iterutils.py")
        content_str = self._read("boltons", "strutils.py")
        combined = content_iter + content_str
        isinstance_count = len(re.findall(r"isinstance\s*\(", combined))
        assert isinstance_count >= 1, (
            "Neither file uses isinstance() — expected type checks to be "
            "refactored from type(x)==... to isinstance()"
        )

    # ------------------------------------------------------------------
    # L2: Existing tests still pass
    # ------------------------------------------------------------------

    def test_existing_iterutils_tests_pass(self):
        """Existing tests for iterutils must still pass after refactoring."""
        # Try common test file locations
        test_candidates = [
            "tests/test_iterutils.py",
            "test/test_iterutils.py",
            "boltons/tests/test_iterutils.py",
        ]
        test_file = None
        for candidate in test_candidates:
            fpath = os.path.join(self.REPO_DIR, candidate)
            if os.path.isfile(fpath):
                test_file = candidate
                break
        if test_file is None:
            pytest.skip("No existing iterutils test file found")

        result = subprocess.run(
            ["python", "-m", "pytest", test_file, "-v", "--tb=short", "-x"],
            cwd=self.REPO_DIR,
            capture_output=True,
            text=True,
            timeout=120,
        )
        assert result.returncode == 0, (
            f"Existing iterutils tests failed after refactoring:\n"
            f"{result.stdout[-3000:]}\n{result.stderr[-1000:]}"
        )

    def test_existing_strutils_tests_pass(self):
        """Existing tests for strutils must still pass after refactoring."""
        test_candidates = [
            "tests/test_strutils.py",
            "test/test_strutils.py",
            "boltons/tests/test_strutils.py",
        ]
        test_file = None
        for candidate in test_candidates:
            fpath = os.path.join(self.REPO_DIR, candidate)
            if os.path.isfile(fpath):
                test_file = candidate
                break
        if test_file is None:
            pytest.skip("No existing strutils test file found")

        result = subprocess.run(
            ["python", "-m", "pytest", test_file, "-v", "--tb=short", "-x"],
            cwd=self.REPO_DIR,
            capture_output=True,
            text=True,
            timeout=120,
        )
        assert result.returncode == 0, (
            f"Existing strutils tests failed after refactoring:\n"
            f"{result.stdout[-3000:]}\n{result.stderr[-1000:]}"
        )

    def test_modules_importable(self):
        """Both refactored modules must be importable without errors."""
        result = subprocess.run(
            ["python", "-c", "from boltons import iterutils, strutils; print('OK')"],
            cwd=self.REPO_DIR,
            capture_output=True,
            text=True,
            timeout=30,
        )
        assert (
            result.returncode == 0
        ), f"Import failed after refactoring:\n{result.stderr}"
        assert "OK" in result.stdout
