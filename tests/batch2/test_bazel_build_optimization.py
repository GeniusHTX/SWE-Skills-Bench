"""
Test for 'bazel-build-optimization' skill — Python Bazel Build Example
Validates that the Agent created a Python Bazel example project with
library, binary, and test targets, plus workspace/module configuration.
"""

import os
import re

import pytest


class TestBazelBuildOptimization:
    """Verify Python Bazel build example."""

    REPO_DIR = "/workspace/bazel"
    EXAMPLE_DIR = "examples/python-bazel"

    def _read(self, *parts):
        fpath = os.path.join(self.REPO_DIR, *parts)
        assert os.path.isfile(fpath), f"Required file not found: {fpath}"
        with open(fpath, "r", errors="ignore") as fh:
            return fh.read()

    def _find_build_file(self):
        """Find BUILD or BUILD.bazel file."""
        for name in ("BUILD.bazel", "BUILD"):
            fpath = os.path.join(self.REPO_DIR, self.EXAMPLE_DIR, name)
            if os.path.isfile(fpath):
                return fpath
        pytest.fail("Neither BUILD nor BUILD.bazel found")

    def _find_workspace_file(self):
        """Find WORKSPACE.bazel or MODULE.bazel file."""
        for name in ("MODULE.bazel", "WORKSPACE.bazel", "WORKSPACE"):
            fpath = os.path.join(self.REPO_DIR, self.EXAMPLE_DIR, name)
            if os.path.isfile(fpath):
                return fpath
        pytest.fail("Neither WORKSPACE nor MODULE.bazel found")

    # ------------------------------------------------------------------
    # L1: File existence
    # ------------------------------------------------------------------

    def test_example_directory_exists(self):
        """examples/python-bazel/ must exist."""
        assert os.path.isdir(os.path.join(self.REPO_DIR, self.EXAMPLE_DIR))

    def test_build_file_exists(self):
        """BUILD or BUILD.bazel must exist."""
        self._find_build_file()

    def test_workspace_file_exists(self):
        """WORKSPACE or MODULE.bazel must exist."""
        self._find_workspace_file()

    def test_python_source_exists(self):
        """At least one .py source file must exist."""
        example = os.path.join(self.REPO_DIR, self.EXAMPLE_DIR)
        py_files = []
        for root, _dirs, files in os.walk(example):
            for f in files:
                if f.endswith(".py"):
                    py_files.append(f)
        assert len(py_files) >= 1, "No Python source files found"

    # ------------------------------------------------------------------
    # L2: BUILD targets
    # ------------------------------------------------------------------

    def test_has_py_library(self):
        """BUILD must define a py_library target."""
        build = self._find_build_file()
        with open(build, "r", errors="ignore") as fh:
            content = fh.read()
        assert re.search(r"py_library\(", content), "No py_library target in BUILD"

    def test_has_py_binary(self):
        """BUILD must define a py_binary target."""
        build = self._find_build_file()
        with open(build, "r", errors="ignore") as fh:
            content = fh.read()
        assert re.search(r"py_binary\(", content), "No py_binary target in BUILD"

    def test_has_py_test(self):
        """BUILD must define a py_test target."""
        build = self._find_build_file()
        with open(build, "r", errors="ignore") as fh:
            content = fh.read()
        assert re.search(r"py_test\(", content), "No py_test target in BUILD"

    def test_binary_depends_on_library(self):
        """py_binary should depend on the py_library."""
        build = self._find_build_file()
        with open(build, "r", errors="ignore") as fh:
            content = fh.read()
        # Look for deps with a library reference
        assert re.search(r"deps\s*=\s*\[", content), "py_binary has no deps"

    # ------------------------------------------------------------------
    # L2: Workspace configuration
    # ------------------------------------------------------------------

    def test_workspace_configures_rules_python(self):
        """Workspace/Module must configure rules_python."""
        ws = self._find_workspace_file()
        with open(ws, "r", errors="ignore") as fh:
            content = fh.read()
        patterns = [
            r"rules_python",
            r"python_register_toolchains",
            r"pip_parse",
            r"pip\.parse",
            r"python.*toolchain",
        ]
        assert any(
            re.search(p, content) for p in patterns
        ), "Workspace does not configure rules_python"

    def test_workspace_pins_python_version(self):
        """Workspace must pin a Python interpreter version."""
        ws = self._find_workspace_file()
        with open(ws, "r", errors="ignore") as fh:
            content = fh.read()
        patterns = [r"python_version", r"3\.\d+", r"interpreter"]
        assert any(
            re.search(p, content) for p in patterns
        ), "Workspace does not pin Python version"

    # ------------------------------------------------------------------
    # L2: Test target
    # ------------------------------------------------------------------

    def test_test_file_exists(self):
        """At least one Python test file must exist."""
        example = os.path.join(self.REPO_DIR, self.EXAMPLE_DIR)
        test_files = []
        for root, _dirs, files in os.walk(example):
            for f in files:
                if f.startswith("test_") and f.endswith(".py"):
                    test_files.append(f)
                elif f.endswith("_test.py"):
                    test_files.append(f)
        assert len(test_files) >= 1, "No Python test files found"

    def test_library_has_importable_function(self):
        """Library source must export at least one function or class."""
        example = os.path.join(self.REPO_DIR, self.EXAMPLE_DIR)
        for root, _dirs, files in os.walk(example):
            for f in files:
                if f.endswith(".py") and not f.startswith("test"):
                    with open(os.path.join(root, f), "r", errors="ignore") as fh:
                        text = fh.read()
                    if re.search(r"def\s+\w+|class\s+\w+", text):
                        return
        pytest.fail("No importable function or class in library source")
