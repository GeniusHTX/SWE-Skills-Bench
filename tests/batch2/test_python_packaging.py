"""
Test for 'python-packaging' skill — Python Packaging & Distribution
Validates that the Agent created a demo script exercising the packaging library's
version parsing, specifier matching, and requirement handling capabilities.
"""

import os
import re
import subprocess

import pytest

from _dependency_utils import ensure_python_dependencies


@pytest.fixture(scope="module", autouse=True)
def _ensure_repo_dependencies():
    ensure_python_dependencies(TestPythonPackaging.REPO_DIR)


class TestPythonPackaging:
    """Verify packaging demonstration script."""

    REPO_DIR = "/workspace/packaging"

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    def _read(self, *parts):
        fpath = os.path.join(self.REPO_DIR, *parts)
        assert os.path.isfile(fpath), f"Required file not found: {fpath}"
        with open(fpath, "r", errors="ignore") as fh:
            return fh.read()

    # ------------------------------------------------------------------
    # L1: File existence and syntax
    # ------------------------------------------------------------------

    def test_demo_script_exists(self):
        """scripts/demo_packaging.py must exist."""
        fpath = os.path.join(self.REPO_DIR, "scripts", "demo_packaging.py")
        assert os.path.isfile(fpath), "scripts/demo_packaging.py not found"

    def test_demo_script_compiles(self):
        """demo_packaging.py must be syntactically valid Python."""
        result = subprocess.run(
            ["python", "-m", "py_compile", "scripts/demo_packaging.py"],
            cwd=self.REPO_DIR,
            capture_output=True,
            text=True,
            timeout=30,
        )
        assert (
            result.returncode == 0
        ), f"Syntax error in demo_packaging.py:\n{result.stderr}"

    def test_demo_has_main_entry_point(self):
        """Script must have a __main__ entry point for direct execution."""
        content = self._read("scripts", "demo_packaging.py")
        assert re.search(
            r'if\s+__name__\s*==\s*["\']__main__["\']', content
        ), "demo_packaging.py missing __main__ entry point"

    # ------------------------------------------------------------------
    # L1: Imports from packaging library
    # ------------------------------------------------------------------

    def test_imports_packaging_version(self):
        """Script must import Version from the packaging library."""
        content = self._read("scripts", "demo_packaging.py")
        patterns = [
            r"from\s+packaging\.version\s+import",
            r"from\s+packaging\s+import.*version",
            r"import\s+packaging\.version",
            r"packaging\.version\.Version",
        ]
        assert any(
            re.search(p, content) for p in patterns
        ), "Script does not import version utilities from packaging"

    def test_imports_packaging_specifiers(self):
        """Script must import SpecifierSet or similar from packaging."""
        content = self._read("scripts", "demo_packaging.py")
        patterns = [
            r"from\s+packaging\.specifiers\s+import",
            r"SpecifierSet",
            r"Specifier",
            r"packaging\.specifiers",
        ]
        assert any(
            re.search(p, content) for p in patterns
        ), "Script does not import specifier utilities from packaging"

    def test_imports_packaging_requirements(self):
        """Script must import Requirement from packaging."""
        content = self._read("scripts", "demo_packaging.py")
        patterns = [
            r"from\s+packaging\.requirements\s+import",
            r"Requirement",
            r"packaging\.requirements",
        ]
        assert any(
            re.search(p, content) for p in patterns
        ), "Script does not import requirement utilities from packaging"

    # ------------------------------------------------------------------
    # L1: Content coverage
    # ------------------------------------------------------------------

    def test_demonstrates_version_parsing(self):
        """Script must demonstrate parsing PEP 440 version strings."""
        content = self._read("scripts", "demo_packaging.py")
        patterns = [r"Version\s*\(", r"parse\s*\(", r"version.*parse"]
        assert any(
            re.search(p, content) for p in patterns
        ), "Script does not demonstrate version parsing"

    def test_demonstrates_version_comparison(self):
        """Script must demonstrate version comparison or sorting."""
        content = self._read("scripts", "demo_packaging.py")
        patterns = [
            r"<\s*Version|>\s*Version|Version.*<|Version.*>",
            r"sort",
            r"compare",
            r"==\s*Version",
            r"<|>|<=|>=",
        ]
        assert any(
            re.search(p, content) for p in patterns
        ), "Script does not demonstrate version comparison"

    def test_demonstrates_specifier_matching(self):
        """Script must demonstrate specifier matching (contains/filter)."""
        content = self._read("scripts", "demo_packaging.py")
        patterns = [
            r"SpecifierSet\s*\(",
            r"contains\s*\(",
            r"filter\s*\(",
            r"\bin\b.*SpecifierSet",
            r"specifier",
        ]
        assert any(
            re.search(p, content, re.IGNORECASE) for p in patterns
        ), "Script does not demonstrate specifier matching"

    def test_demonstrates_requirement_parsing(self):
        """Script must demonstrate requirement string parsing."""
        content = self._read("scripts", "demo_packaging.py")
        patterns = [
            r"Requirement\s*\(",
            r"\.name\b",
            r"\.specifier\b",
            r"\.extras\b",
            r"\.marker\b",
        ]
        matches = sum(1 for p in patterns if re.search(p, content))
        assert matches >= 2, (
            "Script does not sufficiently demonstrate requirement parsing "
            "(need Requirement() and at least one attribute access)"
        )

    # ------------------------------------------------------------------
    # L2: Dynamic execution
    # ------------------------------------------------------------------

    def test_script_runs_successfully(self):
        """demo_packaging.py must run to completion without errors."""
        result = subprocess.run(
            ["python", "scripts/demo_packaging.py"],
            cwd=self.REPO_DIR,
            capture_output=True,
            text=True,
            timeout=60,
        )
        assert result.returncode == 0, (
            f"Script failed (rc={result.returncode}):\n"
            f"stdout: {result.stdout[-2000:]}\n"
            f"stderr: {result.stderr[-2000:]}"
        )

    def test_script_produces_structured_output(self):
        """Script output must contain recognizable version/specifier/requirement results."""
        result = subprocess.run(
            ["python", "scripts/demo_packaging.py"],
            cwd=self.REPO_DIR,
            capture_output=True,
            text=True,
            timeout=60,
        )
        output = result.stdout
        # Should contain version strings, comparison results, or match verdicts
        has_version_info = bool(re.search(r"\d+\.\d+", output))
        has_match_info = bool(
            re.search(
                r"match|satisfy|contains|True|False|pass|fail", output, re.IGNORECASE
            )
        )
        assert has_version_info or has_match_info, (
            f"Script output does not contain recognizable version/match information:\n"
            f"{output[:2000]}"
        )

    def test_script_handles_invalid_versions(self):
        """Script should handle invalid version strings gracefully."""
        content = self._read("scripts", "demo_packaging.py")
        # Should contain try/except or InvalidVersion handling
        error_patterns = [
            r"InvalidVersion",
            r"except.*Version",
            r"try.*Version",
            r"invalid",
            r"error.*version",
        ]
        assert any(
            re.search(p, content, re.IGNORECASE) for p in error_patterns
        ), "Script does not handle invalid version strings"

    def test_pre_release_versions_demonstrated(self):
        """Script must include pre-release version examples (alpha, beta, rc, dev)."""
        content = self._read("scripts", "demo_packaging.py")
        pre_release_patterns = [
            r"alpha|a\d",
            r"beta|b\d",
            r"rc\d",
            r"dev\d",
            r"pre",
            r"\.dev",
            r"\.post",
        ]
        matches = sum(
            1 for p in pre_release_patterns if re.search(p, content, re.IGNORECASE)
        )
        assert matches >= 1, "Script does not include pre-release version examples"
