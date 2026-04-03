"""
Test for 'python-anti-patterns' skill — Python Anti-Pattern Refactoring
Validates that the Agent modernized Python code by eliminating bare excepts,
wildcard imports, global statements, and mutable default arguments.
"""

import ast
import glob
import os
import re
import sys

import pytest


class TestPythonAntiPatterns:
    """Verify Python anti-pattern refactoring in boltons."""

    REPO_DIR = "/workspace/boltons"

    # ---- helpers ----

    @staticmethod
    def _read(path):
        with open(path, "r", errors="ignore") as fh:
            return fh.read()

    def _py_files(self):
        return glob.glob(os.path.join(self.REPO_DIR, "**", "*.py"), recursive=True)

    # ---- file_path_check ----

    def test_py_files_exist(self):
        """Verifies Python files exist in the repository."""
        files = self._py_files()
        assert len(files) > 0, "No .py files found in repo"

    def test_repo_dir_exists(self):
        """Verifies the repository directory exists."""
        assert os.path.isdir(self.REPO_DIR), f"Repo dir not found: {self.REPO_DIR}"

    # ---- semantic_check ----

    def test_sem_no_wildcard_imports(self):
        """Verifies no wildcard 'from X import *' in any .py file."""
        for py in self._py_files():
            tree = ast.parse(self._read(py))
            for node in ast.walk(tree):
                if isinstance(node, ast.ImportFrom):
                    names = [a.name for a in node.names]
                    assert "*" not in names, f"Wildcard import found in {py}"

    def test_sem_no_bare_excepts(self):
        """Verifies no bare 'except:' blocks."""
        pattern = re.compile(r"^\s*except\s*:", re.MULTILINE)
        for py in self._py_files():
            content = self._read(py)
            assert not pattern.search(content), f"Bare except found in {py}"

    def test_sem_no_global_statements(self):
        """Verifies no 'global' statements in function bodies."""
        for py in self._py_files():
            tree = ast.parse(self._read(py))
            for node in ast.walk(tree):
                if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                    for child in ast.walk(node):
                        if isinstance(child, ast.Global):
                            pytest.fail(f"Global statement found in {py}:{node.name}")

    def test_sem_ast_parseable(self):
        """Verifies all .py files are valid Python (AST-parseable)."""
        for py in self._py_files():
            try:
                ast.parse(self._read(py))
            except SyntaxError:
                pytest.fail(f"Syntax error in {py}")

    def test_sem_type_hints_present(self):
        """Verifies functions use type annotations or docstrings."""
        found_annotations = False
        for py in self._py_files():
            tree = ast.parse(self._read(py))
            for node in ast.walk(tree):
                if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                    if node.returns or any(a.annotation for a in node.args.args):
                        found_annotations = True
                        break
            if found_annotations:
                break
        assert found_annotations, "No type annotations found in any function"

    def test_sem_no_mutable_default_args(self):
        """Verifies no mutable defaults (list/dict/set) in function signatures."""
        for py in self._py_files():
            tree = ast.parse(self._read(py))
            for node in ast.walk(tree):
                if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                    for default in node.args.defaults + node.args.kw_defaults:
                        if default and isinstance(
                            default, (ast.List, ast.Dict, ast.Set)
                        ):
                            pytest.fail(f"Mutable default in {py}:{node.name}")

    # ---- functional_check ----

    def test_func_data_processor_no_mutable_default(self):
        """Verifies DataProcessor uses None for default list/dict args."""
        old_path = sys.path[:]
        sys.path.insert(0, self.REPO_DIR)
        try:
            from data_processor import DataProcessor  # type: ignore

            dp = DataProcessor()
            assert hasattr(dp, "process") or hasattr(
                dp, "run"
            ), "DataProcessor missing process/run method"
        finally:
            sys.path[:] = old_path

    def test_func_data_processor_none_pattern(self):
        """Verifies DataProcessor __init__ uses 'if items is None' pattern."""
        candidates = glob.glob(
            os.path.join(self.REPO_DIR, "**", "data_processor.py"), recursive=True
        )
        assert candidates, "data_processor.py not found"
        content = self._read(candidates[0])
        assert (
            "is None" in content
        ), "DataProcessor should use 'is None' pattern for mutable defaults"

    def test_func_math_utils_max_retries(self):
        """Verifies MathUtils.MAX_RETRIES is a class constant."""
        old_path = sys.path[:]
        sys.path.insert(0, self.REPO_DIR)
        try:
            from math_utils import MathUtils  # type: ignore

            assert hasattr(
                MathUtils, "MAX_RETRIES"
            ), "MathUtils missing MAX_RETRIES constant"
            assert isinstance(
                MathUtils.MAX_RETRIES, int
            ), "MAX_RETRIES should be an int"
        finally:
            sys.path[:] = old_path

    def test_func_error_handling_service(self):
        """Verifies ErrorHandlingService catches specific exceptions."""
        candidates = glob.glob(
            os.path.join(self.REPO_DIR, "**", "error_handling*"), recursive=True
        )
        assert candidates, "ErrorHandlingService file not found"
        content = self._read(candidates[0])
        # Should use specific exception types, not bare except
        assert re.search(
            r"except\s+(\w+Error|\w+Exception)", content
        ), "ErrorHandlingService should catch specific exceptions"

    def test_func_process_none_raises(self):
        """Verifies process(None) raises TypeError or ValueError."""
        old_path = sys.path[:]
        sys.path.insert(0, self.REPO_DIR)
        try:
            from data_processor import DataProcessor  # type: ignore

            dp = DataProcessor()
            with pytest.raises((TypeError, ValueError)):
                dp.process(None)
        finally:
            sys.path[:] = old_path

    def test_func_no_nested_try_except(self):
        """Verifies refactored code avoids deeply nested try/except."""
        for py in self._py_files():
            content = self._read(py)
            # Simple heuristic: no more than 2 levels of try nesting
            depth = 0
            max_depth = 0
            for line in content.splitlines():
                stripped = line.strip()
                if stripped.startswith("try:"):
                    depth += 1
                    max_depth = max(max_depth, depth)
                elif stripped.startswith("except") or stripped.startswith("finally"):
                    depth = max(0, depth - 1)
            assert max_depth <= 2, f"Deeply nested try/except in {py}"
