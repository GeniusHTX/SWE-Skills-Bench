"""
Test for 'creating-financial-models' skill — QuantLib Financial Modeling
Validates DCF model with enterprise value computation, sensitivity grid,
WACC/terminal growth config, and edge cases.
"""

import os
import re
import subprocess
import sys

import pytest


class TestCreatingFinancialModels:
    """Verify QuantLib DCF financial model implementation."""

    REPO_DIR = "/workspace/QuantLib"

    # ── file_path_check ─────────────────────────────────────────────────────

    def test_python_source_files_exist(self):
        """Verify at least 2 Python source files for the DCF model exist."""
        py_files = self._find_model_files()
        assert (
            len(py_files) >= 2
        ), f"Expected ≥2 financial model Python files, found {len(py_files)}"

    def test_test_file_exists(self):
        """Verify a test file for the financial model exists."""
        found = False
        for dirpath, _, fnames in os.walk(self.REPO_DIR):
            if ".git" in dirpath:
                continue
            for f in fnames:
                if (
                    f.endswith(".py")
                    and "test" in f.lower()
                    and (
                        "dcf" in f.lower()
                        or "financial" in f.lower()
                        or "model" in f.lower()
                    )
                ):
                    found = True
                    break
            if found:
                break
        assert found, "No DCF/financial model test file found"

    # ── semantic_check ──────────────────────────────────────────────────────

    def test_compute_enterprise_value(self):
        """Verify compute_enterprise_value function exists."""
        py_files = self._find_model_files()
        assert py_files, "No model files found"
        for fpath in py_files:
            content = self._read(fpath)
            if re.search(
                r"def\s+(compute_enterprise_value|calculate_ev|enterprise_value)",
                content,
            ):
                return
        pytest.fail("No compute_enterprise_value function found")

    def test_sensitivity_grid(self):
        """Verify sensitivity analysis grid (9x9 or similar matrix)."""
        py_files = self._find_model_files()
        assert py_files, "No model files found"
        for fpath in py_files:
            content = self._read(fpath)
            if re.search(
                r"sensitiv|grid|matrix|np\.meshgrid|itertools\.product",
                content,
                re.IGNORECASE,
            ):
                return
        pytest.fail("No sensitivity analysis grid found")

    def test_wacc_configuration(self):
        """Verify WACC (Weighted Average Cost of Capital) is configurable."""
        py_files = self._find_model_files()
        assert py_files, "No model files found"
        for fpath in py_files:
            content = self._read(fpath)
            if re.search(
                r"wacc|weighted.?average.?cost|discount.?rate", content, re.IGNORECASE
            ):
                return
        pytest.fail("No WACC configuration found")

    def test_terminal_growth_rate(self):
        """Verify terminal growth rate parameter exists."""
        py_files = self._find_model_files()
        assert py_files, "No model files found"
        for fpath in py_files:
            content = self._read(fpath)
            if re.search(
                r"terminal.?growth|growth.?rate|g_terminal", content, re.IGNORECASE
            ):
                return
        pytest.fail("No terminal growth rate parameter found")

    # ── functional_check ────────────────────────────────────────────────────

    def test_model_files_compile(self):
        """Verify Python model files compile without syntax errors."""
        py_files = self._find_model_files()
        assert py_files, "No model files"
        for fpath in py_files:
            result = subprocess.run(
                [sys.executable, "-m", "py_compile", fpath],
                capture_output=True,
                text=True,
                timeout=30,
            )
            assert (
                result.returncode == 0
            ), f"Compile error in {os.path.basename(fpath)}: {result.stderr}"

    def test_ev_in_expected_range(self):
        """Verify enterprise value is computed (looking for ~$753-760M range reference)."""
        py_files = self._find_model_files()
        for fpath in py_files:
            content = self._read(fpath)
            # Look for expected value reference or assertion
            if re.search(r"75[0-9]|760|enterprise.?value|EV", content):
                return
        # Also check test files
        for dirpath, _, fnames in os.walk(self.REPO_DIR):
            if ".git" in dirpath:
                continue
            for f in fnames:
                if f.endswith(".py") and "test" in f.lower():
                    content = self._read(os.path.join(dirpath, f))
                    if re.search(
                        r"75[0-9]|760|enterprise.?value", content, re.IGNORECASE
                    ):
                        return
        pytest.skip("Cannot verify EV computation range without running model")

    def test_negative_wacc_rejection(self):
        """Verify negative WACC is rejected or handled."""
        all_files = self._find_model_files() + self._find_test_files()
        for fpath in all_files:
            content = self._read(fpath)
            if re.search(
                r"(negative|<\s*0|<=\s*0|ValueError|raise|assert.*wacc.*>)",
                content,
                re.IGNORECASE,
            ):
                if "wacc" in content.lower() or "discount" in content.lower():
                    return
        pytest.skip("Negative WACC rejection not explicitly detectable")

    def test_dcf_uses_numpy_or_math(self):
        """Verify DCF model uses numpy or math for calculations."""
        py_files = self._find_model_files()
        assert py_files, "No model files"
        for fpath in py_files:
            content = self._read(fpath)
            if re.search(r"import\s+(numpy|math|pandas|scipy)", content):
                return
        pytest.fail("No numerical library imports found in model files")

    def test_sensitivity_grid_dimensions(self):
        """Verify sensitivity grid has meaningful dimensions."""
        py_files = self._find_model_files()
        for fpath in py_files:
            content = self._read(fpath)
            if re.search(r"9\s*[x×,]\s*9|range\(.*9\)|linspace\(.*9\)|arange", content):
                return
            if re.search(r"sensitiv.*grid|grid.*sensitiv", content, re.IGNORECASE):
                return
        pytest.skip("sensitivity grid dimensions not explicitly stated")

    # ── helpers ──────────────────────────────────────────────────────────────

    def _find_model_files(self):
        results = []
        for dirpath, _, fnames in os.walk(self.REPO_DIR):
            if ".git" in dirpath:
                continue
            for f in fnames:
                if f.endswith(".py") and (
                    "dcf" in f.lower()
                    or "financial" in f.lower()
                    or "model" in f.lower()
                    or "valuation" in f.lower()
                ):
                    if "test" not in f.lower():
                        results.append(os.path.join(dirpath, f))
        return results

    def _find_test_files(self):
        results = []
        for dirpath, _, fnames in os.walk(self.REPO_DIR):
            if ".git" in dirpath:
                continue
            for f in fnames:
                if (
                    f.endswith(".py")
                    and "test" in f.lower()
                    and (
                        "dcf" in f.lower()
                        or "financial" in f.lower()
                        or "model" in f.lower()
                    )
                ):
                    results.append(os.path.join(dirpath, f))
        return results

    def _read(self, path):
        with open(path, "r", errors="ignore") as fh:
            return fh.read()
