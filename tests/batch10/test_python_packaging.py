"""
Test for 'python-packaging' skill — Python packaging best practices
Validates that the Agent implemented proper Python packaging patterns
in the packaging project.
"""

import os
import re

import pytest


class TestPythonPackaging:
    """Verify Python packaging implementation."""

    REPO_DIR = "/workspace/packaging"

    def test_pyproject_toml_exists(self):
        """pyproject.toml must exist."""
        found = False
        for root, dirs, files in os.walk(self.REPO_DIR):
            if "pyproject.toml" in files:
                found = True
                break
        assert found, "pyproject.toml not found"

    def test_build_system_defined(self):
        """pyproject.toml must define build-system."""
        found = False
        for root, dirs, files in os.walk(self.REPO_DIR):
            if "pyproject.toml" in files:
                path = os.path.join(root, "pyproject.toml")
                with open(path, "r", errors="ignore") as fh:
                    content = fh.read()
                if re.search(r"\[build-system\]", content):
                    found = True
                break
        assert found, "No build-system in pyproject.toml"

    def test_project_metadata(self):
        """pyproject.toml must define project metadata (name, version)."""
        found = False
        for root, dirs, files in os.walk(self.REPO_DIR):
            if "pyproject.toml" in files:
                path = os.path.join(root, "pyproject.toml")
                with open(path, "r", errors="ignore") as fh:
                    content = fh.read()
                if re.search(r"name\s*=", content) and re.search(r"version\s*=", content):
                    found = True
                break
        assert found, "No project name/version in pyproject.toml"

    def test_package_directory_exists(self):
        """A Python package directory (with __init__.py) must exist."""
        found = False
        for root, dirs, files in os.walk(self.REPO_DIR):
            if "__init__.py" in files and ".git" not in root:
                found = True
                break
        assert found, "No Python package directory found"

    def test_dependencies_defined(self):
        """Package dependencies must be defined."""
        found = False
        for root, dirs, files in os.walk(self.REPO_DIR):
            for f in files:
                if f in ("pyproject.toml", "setup.cfg", "setup.py", "requirements.txt"):
                    path = os.path.join(root, f)
                    with open(path, "r", errors="ignore") as fh:
                        content = fh.read()
                    if re.search(r"dependencies|install_requires|requires", content):
                        found = True
                        break
            if found:
                break
        assert found, "No dependencies defined"

    def test_license_defined(self):
        """Package must have a license."""
        found = False
        for root, dirs, files in os.walk(self.REPO_DIR):
            for f in files:
                if f.startswith("LICENSE") or f.startswith("LICENCE"):
                    found = True
                    break
            if found:
                break
        if not found:
            for root, dirs, files in os.walk(self.REPO_DIR):
                if "pyproject.toml" in files:
                    path = os.path.join(root, "pyproject.toml")
                    with open(path, "r", errors="ignore") as fh:
                        content = fh.read()
                    if re.search(r"license", content, re.IGNORECASE):
                        found = True
                    break
        assert found, "No license found"

    def test_readme_exists(self):
        """README must exist."""
        found = False
        for root, dirs, files in os.walk(self.REPO_DIR):
            for f in files:
                if f.lower().startswith("readme"):
                    found = True
                    break
            if found:
                break
        assert found, "No README found"

    def test_test_directory_exists(self):
        """Test directory or test files must exist."""
        found = False
        for root, dirs, files in os.walk(self.REPO_DIR):
            for d in dirs:
                if d in ("tests", "test"):
                    found = True
                    break
            for f in files:
                if f.startswith("test_") and f.endswith(".py"):
                    found = True
                    break
            if found:
                break
        assert found, "No test directory or test files found"

    def test_version_accessible(self):
        """Package version must be accessible (__version__ or metadata)."""
        found = False
        for root, dirs, files in os.walk(self.REPO_DIR):
            for f in files:
                if f.endswith(".py"):
                    path = os.path.join(root, f)
                    with open(path, "r", errors="ignore") as fh:
                        content = fh.read()
                    if re.search(r"__version__|version|importlib\.metadata", content):
                        found = True
                        break
            if found:
                break
        assert found, "No version accessible in package"

    def test_entry_points_or_scripts(self):
        """Package may define entry points or console scripts."""
        found = False
        for root, dirs, files in os.walk(self.REPO_DIR):
            for f in files:
                if f in ("pyproject.toml", "setup.cfg", "setup.py"):
                    path = os.path.join(root, f)
                    with open(path, "r", errors="ignore") as fh:
                        content = fh.read()
                    if re.search(r"entry.points|console_scripts|scripts", content):
                        found = True
                        break
            if found:
                break
        # Advisory — not all packages need entry points
        assert isinstance(found, bool)
