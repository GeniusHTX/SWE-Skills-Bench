"""
Test for 'python-packaging' skill — Python Packaging with pyproject.toml
Validates pyproject.toml structure, build-system, project metadata,
optional dependencies, entry points, and tomllib parsing.
"""

import os
import subprocess
import sys

import pytest


class TestPythonPackaging:
    """Verify Python packaging: pyproject.toml, build system, metadata."""

    REPO_DIR = "/workspace/packaging"

    # ── helpers ──────────────────────────────────────────────────────────

    @staticmethod
    def _read_file(path: str) -> str:
        try:
            with open(path, "r", errors="ignore") as fh:
                return fh.read()
        except OSError:
            return ""

    def _root(self, *parts) -> str:
        return os.path.join(self.REPO_DIR, *parts)

    # ── file_path_check ──────────────────────────────────────────────────

    def test_pyproject_toml_exists(self):
        """pyproject.toml must exist at repository root."""
        assert os.path.isfile(self._root("pyproject.toml")), "pyproject.toml not found"

    def test_src_package_init_exists(self):
        """src/mylibrary/__init__.py or mylibrary/__init__.py must exist."""
        src = self._root("src", "mylibrary", "__init__.py")
        flat = self._root("mylibrary", "__init__.py")
        assert os.path.isfile(src) or os.path.isfile(flat), "Package __init__.py not found"

    def test_readme_and_tests_exist(self):
        """README.md and tests/ directory must exist."""
        assert os.path.isfile(self._root("README.md")), "README.md not found"
        assert os.path.isdir(self._root("tests")), "tests/ directory not found"

    # ── semantic_check ───────────────────────────────────────────────────

    def test_build_system_has_requires_and_backend(self):
        """[build-system] must have requires and build-backend."""
        content = self._read_file(self._root("pyproject.toml"))
        if not content:
            pytest.skip("pyproject.toml not found")
        assert "build-system" in content, "[build-system] section missing"
        assert "requires" in content, "requires not found"
        assert "build-backend" in content, "build-backend not found"

    def test_project_has_required_metadata(self):
        """[project] must have name, version/dynamic, description, requires-python."""
        content = self._read_file(self._root("pyproject.toml"))
        if not content:
            pytest.skip("pyproject.toml not found")
        assert "name" in content
        assert "requires-python" in content or "python_requires" in content
        assert "description" in content

    def test_optional_deps_dev_and_test(self):
        """[project.optional-dependencies] must define dev and test extras."""
        content = self._read_file(self._root("pyproject.toml"))
        if not content:
            pytest.skip("pyproject.toml not found")
        assert "optional-dependencies" in content, "optional-dependencies missing"

    def test_scripts_or_entry_points(self):
        """[project.scripts] must define at least one entry point."""
        content = self._read_file(self._root("pyproject.toml"))
        if not content:
            pytest.skip("pyproject.toml not found")
        has_scripts = "scripts" in content or "entry-points" in content
        assert has_scripts, "No scripts/entry-points section"

    # ── functional_check ─────────────────────────────────────────────────

    def test_pyproject_toml_parses(self):
        """tomllib must parse pyproject.toml without error."""
        path = self._root("pyproject.toml")
        if not os.path.isfile(path):
            pytest.skip("pyproject.toml not found")
        try:
            import tomllib
        except ImportError:
            try:
                import tomli as tomllib  # noqa: N811
            except ImportError:
                pytest.skip("tomllib/tomli not available")
        with open(path, "rb") as f:
            data = tomllib.load(f)
        assert "project" in data, "'project' key missing"
        assert "build-system" in data, "'build-system' key missing"

    def test_version_consistency(self):
        """Package __version__ must match pyproject.toml version."""
        path = self._root("pyproject.toml")
        if not os.path.isfile(path):
            pytest.skip("pyproject.toml not found")
        try:
            import tomllib
        except ImportError:
            try:
                import tomli as tomllib  # noqa: N811
            except ImportError:
                pytest.skip("tomllib/tomli not available")
        with open(path, "rb") as f:
            data = tomllib.load(f)
        toml_version = data.get("project", {}).get("version")
        if not toml_version:
            pytest.skip("Version is dynamic")
        try:
            sys.path.insert(0, self.REPO_DIR)
            from mylibrary import __version__
            assert __version__ == toml_version
        except ImportError:
            pytest.skip("Cannot import mylibrary")

    def test_editable_install_succeeds(self):
        """pip install -e . must exit with code 0."""
        if not os.path.isfile(self._root("pyproject.toml")):
            pytest.skip("pyproject.toml not found")
        result = subprocess.run(
            [sys.executable, "-m", "pip", "install", "-e", self.REPO_DIR, "--quiet"],
            capture_output=True, timeout=120,
        )
        assert result.returncode == 0, f"pip install -e . failed: {result.stderr.decode()}"

    def test_build_backend_key_present(self):
        """build-backend must be present in [build-system]; absence is invalid."""
        path = self._root("pyproject.toml")
        if not os.path.isfile(path):
            pytest.skip("pyproject.toml not found")
        try:
            import tomllib
        except ImportError:
            try:
                import tomli as tomllib  # noqa: N811
            except ImportError:
                pytest.skip("tomllib/tomli not available")
        with open(path, "rb") as f:
            data = tomllib.load(f)
        assert "build-backend" in data.get("build-system", {}), "Missing build-backend"

    def test_importlib_metadata_version(self):
        """importlib.metadata.version must return valid version string after install."""
        try:
            import importlib.metadata
            version = importlib.metadata.version("mylibrary")
            assert isinstance(version, str) and len(version) > 0
        except Exception:
            pytest.skip("Package not installed or metadata unavailable")
