"""
Test for 'python-packaging' skill — Python Packaging & Distribution
Validates that the Agent added version parsing edge case tests and a demo script
to the packaging repository.
"""

import os
import subprocess
import pytest


class TestPythonPackaging:
    """Verify version parsing edge-case tests and demo for packaging."""

    REPO_DIR = "/workspace/packaging"

    # ------------------------------------------------------------------
    # L1: file existence & syntax
    # ------------------------------------------------------------------

    def test_edge_case_tests_exist(self):
        """tests/test_version_edge_cases.py must exist."""
        fpath = os.path.join(self.REPO_DIR, "tests", "test_version_edge_cases.py")
        assert os.path.isfile(fpath), "test_version_edge_cases.py not found"

    def test_demo_script_exists(self):
        """scripts/demo_packaging.py must exist."""
        fpath = os.path.join(self.REPO_DIR, "scripts", "demo_packaging.py")
        assert os.path.isfile(fpath), "demo_packaging.py not found"

    def test_edge_case_tests_compile(self):
        """Edge case test file must compile."""
        result = subprocess.run(
            ["python", "-m", "py_compile", "tests/test_version_edge_cases.py"],
            cwd=self.REPO_DIR,
            capture_output=True,
            text=True,
            timeout=30,
        )
        assert result.returncode == 0, f"Syntax error:\n{result.stderr}"

    def test_demo_script_compiles(self):
        """Demo script must compile."""
        result = subprocess.run(
            ["python", "-m", "py_compile", "scripts/demo_packaging.py"],
            cwd=self.REPO_DIR,
            capture_output=True,
            text=True,
            timeout=30,
        )
        assert result.returncode == 0, f"Syntax error:\n{result.stderr}"

    # ------------------------------------------------------------------
    # L2: functional verification
    # ------------------------------------------------------------------

    def test_demo_script_runs(self):
        """Demo script must run successfully and produce output."""
        result = subprocess.run(
            ["python", "scripts/demo_packaging.py"],
            cwd=self.REPO_DIR,
            capture_output=True,
            text=True,
            timeout=120,
        )
        assert result.returncode == 0, f"Demo failed:\n{result.stderr}"
        assert len(result.stdout.strip()) > 0, "Demo produced no output"

    def test_edge_case_tests_pass(self):
        """Edge case version tests must pass."""
        result = subprocess.run(
            [
                "python",
                "-m",
                "pytest",
                "tests/test_version_edge_cases.py",
                "-v",
                "--tb=short",
            ],
            cwd=self.REPO_DIR,
            capture_output=True,
            text=True,
            timeout=120,
        )
        assert (
            result.returncode == 0
        ), f"Edge case tests failed:\n{result.stdout[-2000:]}\n{result.stderr[-500:]}"

    def test_prerelease_versions_covered(self):
        """Tests must cover pre-release versions (alpha, beta, rc)."""
        fpath = os.path.join(self.REPO_DIR, "tests", "test_version_edge_cases.py")
        with open(fpath, "r", encoding="utf-8") as f:
            content = f.read()
        prerelease_terms = ["a1", "b2", "rc1", "alpha", "beta", "pre"]
        found = sum(1 for t in prerelease_terms if t in content)
        assert found >= 2, f"Insufficient pre-release version coverage (found {found})"

    def test_epoch_version_covered(self):
        """Tests must cover epoch versions (e.g. 1!2.0)."""
        fpath = os.path.join(self.REPO_DIR, "tests", "test_version_edge_cases.py")
        with open(fpath, "r", encoding="utf-8") as f:
            content = f.read()
        assert (
            "!" in content or "epoch" in content.lower()
        ), "Epoch version test case not found"

    def test_local_version_covered(self):
        """Tests must cover local version identifiers (e.g. 1.0+local)."""
        fpath = os.path.join(self.REPO_DIR, "tests", "test_version_edge_cases.py")
        with open(fpath, "r", encoding="utf-8") as f:
            content = f.read()
        assert (
            "+" in content or "local" in content.lower()
        ), "Local version identifier test case not found"

    def test_post_and_dev_versions_covered(self):
        """Tests must cover post-release and dev versions."""
        fpath = os.path.join(self.REPO_DIR, "tests", "test_version_edge_cases.py")
        with open(fpath, "r", encoding="utf-8") as f:
            content = f.read()
        assert (
            "post" in content.lower() or "dev" in content.lower()
        ), "Post-release/dev version test cases not found"

    def test_demo_shows_comparison(self):
        """Demo output should demonstrate version comparison."""
        result = subprocess.run(
            ["python", "scripts/demo_packaging.py"],
            cwd=self.REPO_DIR,
            capture_output=True,
            text=True,
            timeout=120,
        )
        if result.returncode != 0:
            pytest.skip(f"Demo failed: {result.stderr[:500]}")
        output = result.stdout
        # Should show comparison operators or version ordering
        comparison_indicators = [">", "<", "==", "True", "False", "Version"]
        found = sum(1 for ind in comparison_indicators if ind in output)
        assert found >= 2, f"Demo output lacks version comparison results"
