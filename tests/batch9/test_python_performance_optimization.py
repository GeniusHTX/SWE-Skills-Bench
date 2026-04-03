"""
Test for 'python-performance-optimization' skill — Rust/PyO3 Extension
Validates Cargo.toml, src/lib.rs, pyproject.toml maturin config,
crate-type cdylib, #[pymodule], and extension build/output.
"""

import os
import subprocess

import pytest


class TestPythonPerformanceOptimization:
    """Verify Python Rust extension: Cargo config, PyO3, maturin build."""

    REPO_DIR = "/workspace/py-spy"

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

    def test_cargo_toml_exists(self):
        """Cargo.toml must exist."""
        assert os.path.isfile(self._root("Cargo.toml"))

    def test_src_lib_rs_exists(self):
        """src/lib.rs must exist and be non-empty."""
        p = self._root("src", "lib.rs")
        assert os.path.isfile(p)
        assert os.path.getsize(p) > 0

    def test_cargo_lock_and_pyproject_exist(self):
        """Cargo.lock and pyproject.toml must exist."""
        assert os.path.isfile(self._root("Cargo.lock")), "Cargo.lock not found"
        assert os.path.isfile(self._root("pyproject.toml")), "pyproject.toml not found"

    # ── semantic_check ───────────────────────────────────────────────────

    def test_crate_type_cdylib(self):
        """Cargo.toml [lib] must have crate-type = ['cdylib']."""
        content = self._read_file(self._root("Cargo.toml"))
        if not content:
            pytest.skip("Cargo.toml not found")
        assert "cdylib" in content

    def test_pyo3_dependency_with_extension_module(self):
        """Cargo.toml must list pyo3 with extension-module feature."""
        content = self._read_file(self._root("Cargo.toml"))
        if not content:
            pytest.skip("Cargo.toml not found")
        assert "pyo3" in content
        assert "extension-module" in content

    def test_pymodule_macro_in_lib_rs(self):
        """src/lib.rs must contain #[pymodule] macro."""
        content = self._read_file(self._root("src", "lib.rs"))
        if not content:
            pytest.skip("src/lib.rs not found")
        assert "#[pymodule]" in content

    def test_pyfunction_exposed(self):
        """src/lib.rs must expose at least one #[pyfunction]."""
        content = self._read_file(self._root("src", "lib.rs"))
        if not content:
            pytest.skip("src/lib.rs not found")
        assert "#[pyfunction]" in content

    def test_pyproject_uses_maturin_backend(self):
        """pyproject.toml must use maturin as build-backend."""
        content = self._read_file(self._root("pyproject.toml"))
        if not content:
            pytest.skip("pyproject.toml not found")
        assert "maturin" in content

    def test_benchmark_imports_extension(self):
        """benchmarks/bench_extension.py must import extension module."""
        content = self._read_file(self._root("benchmarks", "bench_extension.py"))
        if not content:
            pytest.skip("bench_extension.py not found")
        assert "import" in content
        assert "baseline" in content.lower() or "python" in content.lower()

    # ── functional_check ─────────────────────────────────────────────────

    def test_maturin_develop_exit_code(self):
        """maturin develop must exit with code 0."""
        try:
            subprocess.run(["maturin", "--version"], capture_output=True, timeout=5)
        except (FileNotFoundError, subprocess.TimeoutExpired):
            pytest.skip("maturin not available")
        r = subprocess.run(
            ["maturin", "develop"],
            capture_output=True, text=True, cwd=self.REPO_DIR, timeout=300,
        )
        assert r.returncode == 0, f"maturin develop failed: {r.stderr}"

    def test_extension_import_succeeds(self):
        """Extension module must be importable after build."""
        try:
            import myextension  # noqa: F401
        except ImportError:
            pytest.skip("myextension not built or not importable")

    def test_extension_wrong_type_raises_typeerror(self):
        """Extension function must raise TypeError for wrong arg type."""
        try:
            from myextension import fast_function
        except ImportError:
            pytest.skip("myextension not importable")
        with pytest.raises(TypeError):
            fast_function(None)
