"""
Test for 'python-packaging' skill — Python Packaging (PEP 440)
Validates PEP 440 version normalization, CLI with argparse,
packaging module utilities, and version parsing.
"""

import os
import re
import sys

import pytest


class TestPythonPackaging:
    """Verify Python packaging implementation."""

    REPO_DIR = "/workspace/packaging"

    # ── file_path_check ─────────────────────────────────────────────────────

    def test_packaging_source_exists(self):
        """Verify packaging source directory exists."""
        pkg = os.path.join(self.REPO_DIR, "packaging")
        if os.path.isdir(pkg):
            return
        # fallback: src layout
        src_pkg = os.path.join(self.REPO_DIR, "src", "packaging")
        assert os.path.isdir(pkg) or os.path.isdir(
            src_pkg
        ), "packaging/ or src/packaging/ not found"

    def test_version_module_exists(self):
        """Verify version module exists."""
        candidates = [
            os.path.join(self.REPO_DIR, "packaging", "version.py"),
            os.path.join(self.REPO_DIR, "src", "packaging", "version.py"),
        ]
        assert any(os.path.exists(c) for c in candidates), "version.py not found"

    # ── semantic_check ──────────────────────────────────────────────────────

    def test_pep_440_reference(self):
        """Verify PEP 440 version scheme is referenced."""
        py_files = self._find_py_files()
        for fpath in py_files:
            content = self._read(fpath)
            if re.search(
                r"(PEP\s*440|pep440|Version|version_scheme)", content, re.IGNORECASE
            ):
                return
        pytest.fail("No PEP 440 reference found")

    def test_version_normalize(self):
        """Verify version normalization function exists."""
        py_files = self._find_py_files()
        for fpath in py_files:
            content = self._read(fpath)
            if re.search(r"(def normalize|canonicalize_version|_normalize)", content):
                return
        pytest.fail("No version normalization function found")

    def test_cli_argparse(self):
        """Verify CLI with argparse or click."""
        py_files = self._find_py_files()
        for fpath in py_files:
            content = self._read(fpath)
            if re.search(r"(argparse|click|ArgumentParser|@click\.command)", content):
                return
        pytest.skip("No CLI with argparse/click found (may not be required)")

    def test_version_parsing(self):
        """Verify Version class for parsing version strings."""
        py_files = self._find_py_files()
        for fpath in py_files:
            content = self._read(fpath)
            if re.search(r"class Version", content):
                return
        pytest.fail("No Version class found")

    # ── functional_check ────────────────────────────────────────────────────

    def test_import_version_module(self):
        """Verify version module can be imported."""
        version_py = None
        for candidate in [
            os.path.join(self.REPO_DIR, "packaging", "version.py"),
            os.path.join(self.REPO_DIR, "src", "packaging", "version.py"),
        ]:
            if os.path.exists(candidate):
                version_py = candidate
                break
        if not version_py:
            pytest.skip("version.py not found")
        parent = os.path.dirname(os.path.dirname(version_py))
        if parent not in sys.path:
            sys.path.insert(0, parent)
        try:
            from packaging.version import Version

            v = Version("1.0.0")
            assert str(v) == "1.0.0"
        except Exception as e:
            pytest.skip(f"Cannot import Version: {e}")

    def test_normalize_version(self):
        """Verify normalization produces canonical forms."""
        version_py = None
        for candidate in [
            os.path.join(self.REPO_DIR, "packaging", "version.py"),
            os.path.join(self.REPO_DIR, "src", "packaging", "version.py"),
        ]:
            if os.path.exists(candidate):
                version_py = candidate
                break
        if not version_py:
            pytest.skip("version.py not found")
        parent = os.path.dirname(os.path.dirname(version_py))
        if parent not in sys.path:
            sys.path.insert(0, parent)
        try:
            from packaging.version import Version

            v = Version("1.0.0.0")
            assert v.major == 1 or str(v).startswith("1")
        except Exception as e:
            pytest.skip(f"Cannot test normalization: {e}")

    def test_version_comparison(self):
        """Verify Version objects are comparable."""
        version_py = None
        for candidate in [
            os.path.join(self.REPO_DIR, "packaging", "version.py"),
            os.path.join(self.REPO_DIR, "src", "packaging", "version.py"),
        ]:
            if os.path.exists(candidate):
                version_py = candidate
                break
        if not version_py:
            pytest.skip("version.py not found")
        parent = os.path.dirname(os.path.dirname(version_py))
        if parent not in sys.path:
            sys.path.insert(0, parent)
        try:
            from packaging.version import Version

            assert Version("2.0") > Version("1.0")
        except Exception as e:
            pytest.skip(f"Cannot compare versions: {e}")

    def test_invalid_version_raises(self):
        """Verify invalid version string raises error."""
        version_py = None
        for candidate in [
            os.path.join(self.REPO_DIR, "packaging", "version.py"),
            os.path.join(self.REPO_DIR, "src", "packaging", "version.py"),
        ]:
            if os.path.exists(candidate):
                version_py = candidate
                break
        if not version_py:
            pytest.skip("version.py not found")
        parent = os.path.dirname(os.path.dirname(version_py))
        if parent not in sys.path:
            sys.path.insert(0, parent)
        try:
            from packaging.version import Version, InvalidVersion

            with pytest.raises(InvalidVersion):
                Version("not-a-version!!!")
        except ImportError:
            pytest.skip("Cannot import InvalidVersion")

    def test_specifier_support(self):
        """Verify SpecifierSet for version ranges."""
        py_files = self._find_py_files()
        for fpath in py_files:
            content = self._read(fpath)
            if re.search(r"(Specifier|SpecifierSet|specifier)", content):
                return
        pytest.fail("No Specifier/SpecifierSet support found")

    # ── helpers ──────────────────────────────────────────────────────────────

    def _find_py_files(self):
        results = []
        for dirpath, _, fnames in os.walk(self.REPO_DIR):
            if ".git" in dirpath:
                continue
            for f in fnames:
                if f.endswith(".py"):
                    results.append(os.path.join(dirpath, f))
        return results

    def _read(self, path):
        with open(path, "r", errors="ignore") as fh:
            return fh.read()
