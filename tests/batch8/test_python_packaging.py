"""
Test for 'python-packaging' skill — Python Packaging Standards
Validates that the Agent set up a modern Python package with pyproject.toml,
hatchling build backend, PEP 561 py.typed marker, and CLI entry point.
"""

import os
import re
import subprocess

import pytest


class TestPythonPackaging:
    """Verify Python packaging standards implementation."""

    REPO_DIR = "/workspace/packaging"

    @staticmethod
    def _read(path: str) -> str:
        try:
            with open(path, "r", errors="ignore") as fh:
                return fh.read()
        except OSError:
            return ""

    # ── file_path_check ─────────────────────────────────────────────

    def test_pyproject_toml_exists(self):
        """Verify pyproject.toml exists at the project root."""
        path = os.path.join(self.REPO_DIR, "pyproject.toml")
        assert os.path.isfile(path), "Missing: pyproject.toml"

    def test_py_typed_marker_exists(self):
        """Verify src/mypackage/py.typed PEP 561 marker file exists."""
        path = os.path.join(self.REPO_DIR, "src/mypackage/py.typed")
        assert os.path.isfile(path), "Missing: src/mypackage/py.typed"

    def test_package_init_exists(self):
        """Verify src/mypackage/__init__.py exists with __version__ attribute."""
        path = os.path.join(self.REPO_DIR, "src/mypackage/__init__.py")
        assert os.path.isfile(path), "Missing: src/mypackage/__init__.py"

    # ── semantic_check ──────────────────────────────────────────────

    def test_hatchling_build_backend(self):
        """Verify pyproject.toml declares hatchling as build backend."""
        content = self._read(os.path.join(self.REPO_DIR, "pyproject.toml"))
        assert content, "pyproject.toml is empty or unreadable"
        assert "hatchling" in content, "hatchling not found"
        assert "build-backend" in content, "build-backend not found"

    def test_requires_python_310(self):
        """Verify requires-python is set to >= '3.10'."""
        content = self._read(os.path.join(self.REPO_DIR, "pyproject.toml"))
        assert content, "pyproject.toml is empty or unreadable"
        assert "requires-python" in content, "requires-python not found"
        assert "3.10" in content, "3.10 not found in requires-python"

    def test_cli_entry_point_defined(self):
        """Verify [project.scripts] section defines at least one CLI entry point."""
        content = self._read(os.path.join(self.REPO_DIR, "pyproject.toml"))
        assert content, "pyproject.toml is empty or unreadable"
        assert "[project.scripts]" in content, "[project.scripts] section not found"

    # ── functional_check (command) ──────────────────────────────────

    def _skip_unless_repo(self):
        if not os.path.isdir(self.REPO_DIR):
            pytest.skip("Repo dir does not exist")

    def test_editable_install_exits_zero(self):
        """pip install -e . succeeds with exit code 0."""
        self._skip_unless_repo()
        result = subprocess.run(
            ["pip", "install", "-e", "."],
            capture_output=True, text=True, cwd=self.REPO_DIR, timeout=120,
        )
        assert result.returncode == 0, f"pip install -e . failed: {result.stderr}"

    def test_import_package_exits_zero(self):
        """After editable install, importing mypackage and printing __version__ exits 0."""
        self._skip_unless_repo()
        result = subprocess.run(
            ["python", "-c", "import mypackage; print(mypackage.__version__)"],
            capture_output=True, text=True, cwd=self.REPO_DIR, timeout=30,
        )
        assert result.returncode == 0, f"import failed: {result.stderr}"

    def test_cli_help_exits_zero(self):
        """The installed CLI entry point --help exits 0."""
        self._skip_unless_repo()
        result = subprocess.run(
            ["mypackage", "--help"],
            capture_output=True, text=True, cwd=self.REPO_DIR, timeout=30,
        )
        assert result.returncode == 0, f"CLI --help failed: {result.stderr}"

    def test_importlib_metadata_version_returns_string(self):
        """importlib.metadata.version('mypackage') returns a non-empty string."""
        self._skip_unless_repo()
        result = subprocess.run(
            ["python", "-c",
             "import importlib.metadata; v = importlib.metadata.version('mypackage'); "
             "assert isinstance(v, str) and len(v) > 0"],
            capture_output=True, text=True, cwd=self.REPO_DIR, timeout=30,
        )
        assert result.returncode == 0, f"metadata version check failed: {result.stderr}"
