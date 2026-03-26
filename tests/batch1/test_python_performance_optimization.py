"""
Test for 'python-performance-optimization' skill — Python Profiling Demo Scripts
Validates that the Agent created profiling target scripts and analysis tools
for py-spy.
"""

import os
import subprocess
import pytest


class TestPythonPerformanceOptimization:
    """Verify profiling demo scripts for py-spy."""

    REPO_DIR = "/workspace/py-spy"

    # ------------------------------------------------------------------
    # L1: file existence
    # ------------------------------------------------------------------

    def test_cpu_bound_exists(self):
        """examples/profiling_targets/cpu_bound.py must exist."""
        fpath = os.path.join(
            self.REPO_DIR, "examples", "profiling_targets", "cpu_bound.py"
        )
        assert os.path.isfile(fpath), "cpu_bound.py not found"

    def test_io_bound_exists(self):
        """examples/profiling_targets/io_bound.py must exist."""
        fpath = os.path.join(
            self.REPO_DIR, "examples", "profiling_targets", "io_bound.py"
        )
        assert os.path.isfile(fpath), "io_bound.py not found"

    def test_readme_exists(self):
        """examples/profiling_targets/README.md must exist."""
        fpath = os.path.join(
            self.REPO_DIR, "examples", "profiling_targets", "README.md"
        )
        assert os.path.isfile(fpath), "README.md not found"

    def test_analyze_script_exists(self):
        """scripts/analyze_profile.py must exist."""
        fpath = os.path.join(self.REPO_DIR, "scripts", "analyze_profile.py")
        assert os.path.isfile(fpath), "analyze_profile.py not found"

    # ------------------------------------------------------------------
    # L1: syntax
    # ------------------------------------------------------------------

    def test_cpu_bound_compiles(self):
        """cpu_bound.py must compile."""
        result = subprocess.run(
            ["python", "-m", "py_compile", "examples/profiling_targets/cpu_bound.py"],
            cwd=self.REPO_DIR,
            capture_output=True,
            text=True,
            timeout=30,
        )
        assert result.returncode == 0, f"Syntax error:\n{result.stderr}"

    def test_io_bound_compiles(self):
        """io_bound.py must compile."""
        result = subprocess.run(
            ["python", "-m", "py_compile", "examples/profiling_targets/io_bound.py"],
            cwd=self.REPO_DIR,
            capture_output=True,
            text=True,
            timeout=30,
        )
        assert result.returncode == 0, f"Syntax error:\n{result.stderr}"

    def test_analyze_compiles(self):
        """analyze_profile.py must compile."""
        result = subprocess.run(
            ["python", "-m", "py_compile", "scripts/analyze_profile.py"],
            cwd=self.REPO_DIR,
            capture_output=True,
            text=True,
            timeout=30,
        )
        assert result.returncode == 0, f"Syntax error:\n{result.stderr}"

    # ------------------------------------------------------------------
    # L2: runtime & content verification
    # ------------------------------------------------------------------

    def test_cpu_bound_runs(self):
        """cpu_bound.py must run independently without py-spy."""
        result = subprocess.run(
            ["python", "examples/profiling_targets/cpu_bound.py"],
            cwd=self.REPO_DIR,
            capture_output=True,
            text=True,
            timeout=120,
        )
        assert result.returncode == 0, f"cpu_bound.py failed:\n{result.stderr}"

    def test_io_bound_runs(self):
        """io_bound.py must run independently."""
        result = subprocess.run(
            ["python", "examples/profiling_targets/io_bound.py"],
            cwd=self.REPO_DIR,
            capture_output=True,
            text=True,
            timeout=120,
        )
        assert result.returncode == 0, f"io_bound.py failed:\n{result.stderr}"

    def test_cpu_bound_has_hotspot(self):
        """cpu_bound.py should contain identifiable hotspot functions."""
        fpath = os.path.join(
            self.REPO_DIR, "examples", "profiling_targets", "cpu_bound.py"
        )
        with open(fpath, "r", encoding="utf-8") as f:
            content = f.read()
        hotspot_patterns = ["fibonacci", "matrix", "multiply", "prime", "sort", "loop"]
        found = sum(1 for p in hotspot_patterns if p in content.lower())
        assert found >= 1, "No identifiable CPU hotspot functions found"

    def test_readme_explains_usage(self):
        """README.md should explain how to use py-spy with examples."""
        fpath = os.path.join(
            self.REPO_DIR, "examples", "profiling_targets", "README.md"
        )
        with open(fpath, "r", encoding="utf-8") as f:
            content = f.read()
        assert (
            "py-spy" in content.lower() or "py_spy" in content.lower()
        ), "README doesn't mention py-spy"
        assert len(content) >= 100, "README is too short to be useful"
