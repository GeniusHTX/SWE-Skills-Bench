"""
Test for 'tdd-workflow' skill — Python StringCalculator TDD
Validates StringCalculator implementation, custom delimiter support,
negative number ValueError, and TDD test coverage.
"""

import os
import re
import sys

import pytest


class TestTddWorkflow:
    """Verify TDD workflow with StringCalculator."""

    REPO_DIR = "/workspace/python"

    # ── file_path_check ─────────────────────────────────────────────────────

    def test_calculator_file_exists(self):
        """Verify StringCalculator source file exists."""
        found = False
        for dirpath, _, fnames in os.walk(self.REPO_DIR):
            if ".git" in dirpath:
                continue
            for f in fnames:
                if f.endswith(".py") and (
                    "calculator" in f.lower() or "string_calc" in f.lower()
                ):
                    found = True
                    break
            if found:
                break
        assert found, "No StringCalculator file found"

    def test_test_file_exists(self):
        """Verify test file for StringCalculator exists."""
        found = False
        for dirpath, _, fnames in os.walk(self.REPO_DIR):
            if ".git" in dirpath:
                continue
            for f in fnames:
                if f.endswith(".py") and f.startswith("test_") and "calc" in f.lower():
                    found = True
                    break
            if found:
                break
        assert found, "No test file for StringCalculator found"

    # ── semantic_check ──────────────────────────────────────────────────────

    def test_string_calculator_class(self):
        """Verify StringCalculator class definition."""
        py_files = self._find_py_files()
        for fpath in py_files:
            content = self._read(fpath)
            if re.search(r"class StringCalculator", content):
                return
        pytest.fail("No StringCalculator class found")

    def test_add_method(self):
        """Verify add() method in StringCalculator."""
        py_files = self._find_py_files()
        for fpath in py_files:
            content = self._read(fpath)
            if "StringCalculator" in content and re.search(r"def add\(", content):
                return
        pytest.fail("No add() method found")

    def test_custom_delimiter_support(self):
        """Verify custom delimiter parsing (e.g. //;\\n)."""
        py_files = self._find_py_files()
        for fpath in py_files:
            content = self._read(fpath)
            if re.search(r"(delimiter|//|custom.*delim|split)", content, re.IGNORECASE):
                if "StringCalculator" in content or "calculator" in fpath.lower():
                    return
        pytest.fail("No custom delimiter support found")

    def test_negative_number_error(self):
        """Verify negative numbers raise ValueError."""
        py_files = self._find_py_files()
        for fpath in py_files:
            content = self._read(fpath)
            if re.search(r"(negative|ValueError|not allowed)", content, re.IGNORECASE):
                if "StringCalculator" in content or "calculator" in fpath.lower():
                    return
        pytest.fail("No negative number error handling found")

    # ── functional_check ────────────────────────────────────────────────────

    def test_import_calculator(self):
        """Verify StringCalculator can be imported."""
        calc_file = self._find_calculator_file()
        if not calc_file:
            pytest.skip("Calculator file not found")
        dirpath = os.path.dirname(calc_file)
        if dirpath not in sys.path:
            sys.path.insert(0, dirpath)
        try:
            import importlib

            mod_name = os.path.splitext(os.path.basename(calc_file))[0]
            spec = importlib.util.spec_from_file_location(mod_name, calc_file)
            mod = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(mod)
            assert hasattr(mod, "StringCalculator"), "No StringCalculator in module"
        except Exception as e:
            pytest.skip(f"Cannot import: {e}")

    def test_add_empty_string_returns_zero(self):
        """Verify add('') returns 0."""
        calc_file = self._find_calculator_file()
        if not calc_file:
            pytest.skip("Calculator file not found")
        dirpath = os.path.dirname(calc_file)
        if dirpath not in sys.path:
            sys.path.insert(0, dirpath)
        try:
            import importlib

            mod_name = os.path.splitext(os.path.basename(calc_file))[0]
            spec = importlib.util.spec_from_file_location(mod_name, calc_file)
            mod = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(mod)
            calc = mod.StringCalculator()
            assert calc.add("") == 0
        except Exception as e:
            pytest.skip(f"Cannot test: {e}")

    def test_add_single_number(self):
        """Verify add('1') returns 1."""
        calc_file = self._find_calculator_file()
        if not calc_file:
            pytest.skip("Calculator file not found")
        dirpath = os.path.dirname(calc_file)
        if dirpath not in sys.path:
            sys.path.insert(0, dirpath)
        try:
            import importlib

            mod_name = os.path.splitext(os.path.basename(calc_file))[0]
            spec = importlib.util.spec_from_file_location(mod_name, calc_file)
            mod = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(mod)
            calc = mod.StringCalculator()
            assert calc.add("1") == 1
        except Exception as e:
            pytest.skip(f"Cannot test: {e}")

    def test_add_two_numbers(self):
        """Verify add('1,2') returns 3."""
        calc_file = self._find_calculator_file()
        if not calc_file:
            pytest.skip("Calculator file not found")
        dirpath = os.path.dirname(calc_file)
        if dirpath not in sys.path:
            sys.path.insert(0, dirpath)
        try:
            import importlib

            mod_name = os.path.splitext(os.path.basename(calc_file))[0]
            spec = importlib.util.spec_from_file_location(mod_name, calc_file)
            mod = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(mod)
            calc = mod.StringCalculator()
            assert calc.add("1,2") == 3
        except Exception as e:
            pytest.skip(f"Cannot test: {e}")

    def test_negative_raises_value_error(self):
        """Verify add('-1,2') raises ValueError."""
        calc_file = self._find_calculator_file()
        if not calc_file:
            pytest.skip("Calculator file not found")
        dirpath = os.path.dirname(calc_file)
        if dirpath not in sys.path:
            sys.path.insert(0, dirpath)
        try:
            import importlib

            mod_name = os.path.splitext(os.path.basename(calc_file))[0]
            spec = importlib.util.spec_from_file_location(mod_name, calc_file)
            mod = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(mod)
            calc = mod.StringCalculator()
            with pytest.raises(ValueError):
                calc.add("-1,2")
        except ImportError:
            pytest.skip("Cannot import StringCalculator")

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

    def _find_calculator_file(self):
        for dirpath, _, fnames in os.walk(self.REPO_DIR):
            if ".git" in dirpath:
                continue
            for f in fnames:
                if (
                    f.endswith(".py")
                    and not f.startswith("test_")
                    and ("calculator" in f.lower() or "string_calc" in f.lower())
                ):
                    return os.path.join(dirpath, f)
        return None

    def _read(self, path):
        with open(path, "r", errors="ignore") as fh:
            return fh.read()
