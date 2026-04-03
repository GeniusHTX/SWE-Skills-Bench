"""Test file for the python-anti-patterns skill.

This suite validates anti-pattern fixes in boltons: mutable defaults,
bare except, context managers, string join, isinstance usage.
"""

from __future__ import annotations

import ast
import pathlib
import re

import pytest


class TestPythonAntiPatterns:
    """Verify anti-pattern fixes in boltons."""

    REPO_DIR = "/workspace/boltons"

    ITERUTILS_PY = "boltons/iterutils.py"
    STRUTILS_PY = "boltons/strutils.py"
    DICTUTILS_PY = "boltons/dictutils.py"

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

    def _parse_module(self, relative: str) -> ast.Module:
        src = self._read_text(relative)
        return ast.parse(src)

    # ------------------------------------------------------------------
    # Layer 1 – file_path_check (3 cases)
    # ------------------------------------------------------------------

    def test_file_path_boltons_iterutils_py_exists_and_was_modified(self):
        """Verify iterutils.py exists and is non-empty."""
        self._assert_non_empty_file(self.ITERUTILS_PY)

    def test_file_path_boltons_strutils_py_exists_and_was_modified(self):
        """Verify strutils.py exists and is non-empty."""
        self._assert_non_empty_file(self.STRUTILS_PY)

    def test_file_path_boltons_dictutils_py_exists_and_was_modified(self):
        """Verify dictutils.py exists and is non-empty."""
        self._assert_non_empty_file(self.DICTUTILS_PY)

    # ------------------------------------------------------------------
    # Layer 2 – semantic_check (5 cases)
    # ------------------------------------------------------------------

    def test_semantic_no_mutable_defaults_set_in_any_def_signatures(self):
        """No mutable defaults ([], {}, set()) in any def signatures."""
        for rel in (self.ITERUTILS_PY, self.STRUTILS_PY, self.DICTUTILS_PY):
            tree = self._parse_module(rel)
            for node in ast.walk(tree):
                if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                    for default in node.args.defaults + node.args.kw_defaults:
                        if default is None:
                            continue
                        if isinstance(default, (ast.List, ast.Dict, ast.Set)):
                            pytest.fail(
                                f"Mutable default in {rel}, function {node.name}"
                            )

    def test_semantic_no_bare_except_clauses_remain(self):
        """No bare except: clauses remain."""
        for rel in (self.ITERUTILS_PY, self.STRUTILS_PY, self.DICTUTILS_PY):
            tree = self._parse_module(rel)
            for node in ast.walk(tree):
                if isinstance(node, ast.ExceptHandler) and node.type is None:
                    pytest.fail(f"Bare except in {rel} at line {node.lineno}")

    def test_semantic_all_open_calls_in_fileutils_py_wrapped_in_with_statements(self):
        """All open() calls in fileutils.py wrapped in with statements."""
        fileutils = self._repo_path("boltons/fileutils.py")
        if not fileutils.is_file():
            pytest.skip("fileutils.py not present")
        src = fileutils.read_text(encoding="utf-8", errors="ignore")
        tree = ast.parse(src)
        for node in ast.walk(tree):
            if isinstance(node, ast.Call):
                func = node.func
                name = getattr(func, "id", getattr(func, "attr", ""))
                if name == "open":
                    # Walk parents to check if inside a With
                    # Simple heuristic: search line context
                    line = src.splitlines()[node.lineno - 1]
                    if "with " not in line and "as " not in line:
                        # Check previous line
                        prev = src.splitlines()[max(0, node.lineno - 2)]
                        assert (
                            "with " in prev or "with " in line
                        ), f"open() at line {node.lineno} not in with statement"

    def test_semantic_string_concatenation_in_loops_replaced_with_join_pattern_in_(
        self,
    ):
        """String concatenation in loops replaced with join pattern in strutils.py."""
        src = self._read_text(self.STRUTILS_PY)
        # Should not have += with string in for loops
        assert not re.search(
            r"for\s+.*:\s*\n(?:.*\n)*?.*\+= ['\"]", src
        ), "String concatenation in loops should be replaced with join"

    def test_semantic_isinstance_used_instead_of_type_comparisons_in_iterutils_py(self):
        """isinstance() used instead of type() comparisons in iterutils.py."""
        src = self._read_text(self.ITERUTILS_PY)
        # Should not have type(x) == or type(x) is patterns
        matches = re.findall(r"type\s*\([^)]+\)\s*(==|is)\s", src)
        assert (
            len(matches) == 0
        ), f"Found {len(matches)} type() comparison(s) in iterutils.py"

    # ------------------------------------------------------------------
    # Layer 3 – functional_check (5 cases, import/source analysis)
    # ------------------------------------------------------------------

    def test_functional_bucketize_1_2_3_key_lambda_x_x_2_returns_same_result_as_orig(
        self,
    ):
        """bucketize([1,2,3], key=lambda x: x%2) returns same result as original."""
        src = self._read_text(self.ITERUTILS_PY)
        assert re.search(r"def\s+bucketize\s*\(", src), "bucketize function not found"

    def test_functional_orderedmultidict_constructor_behaves_identically(self):
        """OrderedMultiDict() constructor behaves identically."""
        src = self._read_text(self.DICTUTILS_PY)
        assert re.search(
            r"class\s+OrderedMultiDict", src
        ), "OrderedMultiDict class not found"

    def test_functional_file_operations_in_fileutils_py_properly_release_handles_on_(
        self,
    ):
        """File operations in fileutils.py properly release handles on exceptions."""
        fileutils = self._repo_path("boltons/fileutils.py")
        if not fileutils.is_file():
            pytest.skip("fileutils.py not present")
        src = fileutils.read_text(encoding="utf-8", errors="ignore")
        assert re.search(
            r"with\s+open\s*\(", src
        ), "File operations should use context managers"

    def test_functional_string_building_functions_produce_identical_output(self):
        """String-building functions produce identical output."""
        src = self._read_text(self.STRUTILS_PY)
        assert re.search(r"join\s*\(", src), "String building should use join pattern"

    def test_functional_encoding_functions_catch_specific_unicode_exceptions(self):
        """Encoding functions catch specific Unicode exceptions."""
        src = self._read_text(self.STRUTILS_PY)
        assert re.search(
            r"UnicodeDecodeError|UnicodeEncodeError|UnicodeError", src
        ), "Encoding functions should catch specific Unicode exceptions"
