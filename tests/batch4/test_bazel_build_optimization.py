"""
Test for 'bazel-build-optimization' skill — Bazel Build Optimization
Validates WORKSPACE.bazel, BUILD.bazel, .bazelrc, calculator/formatter Python
modules, and Bazel build rules for a Python project.
"""

import os
import re
import glob
import pytest


class TestBazelBuildOptimization:
    """Tests for Bazel build optimization in the bazel repo."""

    REPO_DIR = "/workspace/bazel"

    def _read(self, relpath):
        full = os.path.join(self.REPO_DIR, relpath)
        with open(full, "r", errors="ignore") as f:
            return f.read()

    def _find_base(self):
        """Find the examples/python-bazel directory."""
        base = os.path.join(self.REPO_DIR, "examples", "python-bazel")
        if os.path.isdir(base):
            return base
        return self.REPO_DIR

    # --- File Path Checks ---

    def test_examples_python_bazel_exists(self):
        """Verifies that examples/python-bazel directory exists."""
        path = os.path.join(self.REPO_DIR, "examples", "python-bazel")
        assert os.path.exists(path), f"Expected directory not found: {path}"

    def test_workspace_bazel_exists(self):
        """Verifies that WORKSPACE.bazel file exists."""
        base = self._find_base()
        path = os.path.join(base, "WORKSPACE.bazel")
        assert os.path.exists(path), f"Expected file not found: {path}"

    def test_build_bazel_exists(self):
        """Verifies that BUILD.bazel file exists."""
        base = self._find_base()
        path = os.path.join(base, "BUILD.bazel")
        assert os.path.exists(path), f"Expected file not found: {path}"

    def test_requirements_txt_exists(self):
        """Verifies that requirements.txt exists."""
        base = self._find_base()
        path = os.path.join(base, "requirements.txt")
        assert os.path.exists(path), f"Expected file not found: {path}"

    # --- Semantic Checks ---

    def test_sem_workspace_parseable(self):
        """WORKSPACE.bazel is readable."""
        base = self._find_base()
        ws = open(os.path.join(base, "WORKSPACE.bazel")).read()
        assert len(ws) > 0, "WORKSPACE.bazel is empty"

    def test_sem_workspace_has_rules_python(self):
        """WORKSPACE.bazel references rules_python."""
        base = self._find_base()
        ws = open(os.path.join(base, "WORKSPACE.bazel")).read()
        assert "rules_python" in ws, "rules_python not loaded in WORKSPACE"

    def test_sem_workspace_has_pip_parse(self):
        """WORKSPACE.bazel references pip_parse or pip.parse."""
        base = self._find_base()
        ws = open(os.path.join(base, "WORKSPACE.bazel")).read()
        assert "pip_parse" in ws or "pip.parse" in ws, "pip_parse missing in WORKSPACE"

    def test_sem_workspace_has_workspace_name(self):
        """WORKSPACE.bazel has python_bazel_demo workspace name."""
        base = self._find_base()
        ws = open(os.path.join(base, "WORKSPACE.bazel")).read()
        assert "python_bazel_demo" in ws, "workspace name python_bazel_demo missing"

    def test_sem_bazelrc_readable(self):
        """'.bazelrc' file is readable."""
        base = self._find_base()
        bazelrc = open(os.path.join(base, ".bazelrc")).read()
        assert len(bazelrc) > 0, ".bazelrc is empty"

    def test_sem_bazelrc_has_cache_config(self):
        """'.bazelrc' has --config=cache profile."""
        base = self._find_base()
        bazelrc = open(os.path.join(base, ".bazelrc")).read()
        assert (
            "--config=cache" in bazelrc or "config=cache" in bazelrc
        ), "--config=cache profile missing"

    # --- Functional Checks ---

    def test_func_calculator_py_readable(self):
        """src/lib/calculator.py is readable."""
        base = self._find_base()
        calc = open(os.path.join(base, "src", "lib", "calculator.py")).read()
        assert len(calc) > 0, "calculator.py is empty"

    def test_func_calculator_has_value_error(self):
        """calculator.py raises ValueError for divide by zero."""
        base = self._find_base()
        calc = open(os.path.join(base, "src", "lib", "calculator.py")).read()
        assert "ValueError" in calc, "ValueError not raised in divide function"

    def test_func_calculator_error_message(self):
        """calculator.py has 'Cannot divide by zero' message."""
        base = self._find_base()
        calc = open(os.path.join(base, "src", "lib", "calculator.py")).read()
        assert "Cannot divide by zero" in calc, "Error message mismatch in divide"

    def test_func_calculator_has_all_functions(self):
        """calculator.py has add, subtract, multiply, divide functions."""
        base = self._find_base()
        calc = open(os.path.join(base, "src", "lib", "calculator.py")).read()
        assert "def add" in calc, "add function missing"
        assert "def subtract" in calc, "subtract function missing"
        assert "def multiply" in calc, "multiply function missing"
        assert "def divide" in calc, "divide function missing"

    def test_func_formatter_py_readable(self):
        """src/lib/formatter.py is readable."""
        base = self._find_base()
        fmt = open(os.path.join(base, "src", "lib", "formatter.py")).read()
        assert len(fmt) > 0, "formatter.py is empty"

    def test_func_formatter_has_functions(self):
        """formatter.py has format_result and format_table functions."""
        base = self._find_base()
        fmt = open(os.path.join(base, "src", "lib", "formatter.py")).read()
        assert "def format_result" in fmt, "format_result function missing"
        assert "def format_table" in fmt, "format_table function missing"

    def test_func_lib_build_bazel_readable(self):
        """src/lib/BUILD.bazel is readable."""
        base = self._find_base()
        lib_build = open(os.path.join(base, "src", "lib", "BUILD.bazel")).read()
        assert len(lib_build) > 0, "src/lib/BUILD.bazel is empty"

    def test_func_lib_build_has_py_library(self):
        """src/lib/BUILD.bazel has py_library target for calculator."""
        base = self._find_base()
        lib_build = open(os.path.join(base, "src", "lib", "BUILD.bazel")).read()
        assert "py_library" in lib_build, "py_library missing in BUILD.bazel"
        assert "calculator" in lib_build, "calculator target missing in BUILD.bazel"
