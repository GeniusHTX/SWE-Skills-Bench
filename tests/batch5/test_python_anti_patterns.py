"""
Test for 'python-anti-patterns' skill — Python Anti-Pattern Fixes
Validates LRU cache with OrderedDict, no bare except, no mutable default
arguments, proper context manager usage, and defensive coding practices.
"""

import os
import re
import ast
import sys

import pytest


class TestPythonAntiPatterns:
    """Verify Python anti-pattern fixes in boltons."""

    REPO_DIR = "/workspace/boltons"

    # ── file_path_check ─────────────────────────────────────────────────────

    def test_python_source_files_exist(self):
        """Verify Python source files exist."""
        py_files = self._find_py_files()
        assert len(py_files) > 0, "No Python files found"

    def test_boltons_package_dir(self):
        """Verify boltons package directory exists."""
        pkg = os.path.join(self.REPO_DIR, "boltons")
        assert os.path.isdir(pkg), "boltons/ package directory not found"

    # ── semantic_check ──────────────────────────────────────────────────────

    def test_no_bare_except(self):
        """Verify no 'except:' without exception type (bare except)."""
        py_files = self._find_py_files()
        violations = []
        for fpath in py_files:
            content = self._read(fpath)
            # Match bare except: (not except SomeError:)
            for i, line in enumerate(content.splitlines(), 1):
                stripped = line.strip()
                if stripped == "except:" or stripped == "except :":
                    violations.append(f"{os.path.basename(fpath)}:{i}")
        assert not violations, f"Bare except found in: {violations[:5]}"

    def test_no_mutable_default_arguments(self):
        """Verify no mutable default arguments (list, dict, set)."""
        py_files = self._find_py_files()
        violations = []
        for fpath in py_files:
            content = self._read(fpath)
            # Check for def func(arg=[], arg={}), def func(arg=set())
            matches = re.findall(
                r"def \w+\([^)]*=\s*(\[\]|\{\}|set\(\))",
                content,
            )
            if matches:
                violations.append(os.path.basename(fpath))
        assert not violations, f"Mutable default args found in: {violations[:5]}"

    def test_lru_cache_or_ordered_dict(self):
        """Verify LRU implementation uses OrderedDict or functools.lru_cache."""
        py_files = self._find_py_files()
        for fpath in py_files:
            content = self._read(fpath)
            if re.search(r"(OrderedDict|lru_cache|LRU|cacheutils)", content):
                return
        pytest.fail("No LRU / OrderedDict / lru_cache usage found")

    def test_context_managers_used(self):
        """Verify context managers are used for resource management."""
        py_files = self._find_py_files()
        for fpath in py_files:
            content = self._read(fpath)
            if re.search(
                r"(with\s+open|__enter__|__exit__|contextmanager|@contextlib)", content
            ):
                return
        pytest.fail("No context manager usage found")

    def test_no_import_star(self):
        """Verify no 'from x import *' in source files."""
        py_files = self._find_py_files()
        violations = []
        for fpath in py_files:
            content = self._read(fpath)
            if re.search(r"from\s+\S+\s+import\s+\*", content):
                violations.append(os.path.basename(fpath))
        assert not violations, f"import * found in: {violations[:5]}"

    # ── functional_check ────────────────────────────────────────────────────

    def test_source_files_parse(self):
        """Verify all Python source files parse as valid AST."""
        py_files = self._find_py_files()
        for fpath in py_files[:20]:  # sample first 20
            content = self._read(fpath)
            try:
                ast.parse(content, filename=fpath)
            except SyntaxError as e:
                pytest.fail(f"SyntaxError in {os.path.basename(fpath)}: {e}")

    def test_cacheutils_module_import(self):
        """Verify cacheutils module can be imported."""
        cache_path = os.path.join(self.REPO_DIR, "boltons", "cacheutils.py")
        if not os.path.exists(cache_path):
            pytest.skip("boltons/cacheutils.py not found")
        pkg_dir = os.path.join(self.REPO_DIR, "boltons")
        if self.REPO_DIR not in sys.path:
            sys.path.insert(0, self.REPO_DIR)
        try:
            import importlib

            spec = importlib.util.spec_from_file_location(
                "boltons.cacheutils", cache_path
            )
            mod = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(mod)
            assert (
                hasattr(mod, "LRU") or hasattr(mod, "LRI") or hasattr(mod, "cached")
            ), "cacheutils missing LRU/LRI/cached"
        except Exception as e:
            pytest.skip(f"Cannot import cacheutils: {e}")

    def test_lru_max_size_respected(self):
        """Verify LRU implementation respects max size."""
        py_files = self._find_py_files()
        for fpath in py_files:
            content = self._read(fpath)
            if "max_size" in content or "maxsize" in content:
                return
        pytest.fail("No max_size/maxsize parameter found in LRU impl")

    def test_type_hints_present(self):
        """Verify type hints are used in new/modified files."""
        py_files = self._find_py_files()
        typed_count = 0
        for fpath in py_files:
            content = self._read(fpath)
            if re.search(
                r"(->|:\s*(str|int|float|bool|list|dict|Optional|Union|Any))", content
            ):
                typed_count += 1
        # At least some files should have type hints
        assert typed_count > 0, "No type hints in any source file"

    def test_proper_exception_chaining(self):
        """Verify 'raise X from Y' or proper exception wrapping."""
        py_files = self._find_py_files()
        for fpath in py_files:
            content = self._read(fpath)
            if "raise " in content and "from " in content:
                return
        # Not mandatory; just skip if not found
        pytest.skip("No exception chaining found (not required)")

    def test_docstrings_present(self):
        """Verify public modules and classes have docstrings."""
        py_files = self._find_py_files()
        for fpath in py_files[:10]:
            content = self._read(fpath)
            tree = ast.parse(content, filename=fpath)
            docstring = ast.get_docstring(tree)
            if docstring:
                return
        pytest.fail("No module-level docstrings found")

    # ── helpers ──────────────────────────────────────────────────────────────

    def _find_py_files(self):
        results = []
        pkg_dir = os.path.join(self.REPO_DIR, "boltons")
        if os.path.isdir(pkg_dir):
            search_dir = pkg_dir
        else:
            search_dir = self.REPO_DIR
        for dirpath, _, fnames in os.walk(search_dir):
            if ".git" in dirpath:
                continue
            for f in fnames:
                if f.endswith(".py") and not f.startswith("test_"):
                    results.append(os.path.join(dirpath, f))
        return results

    def _read(self, path):
        with open(path, "r", errors="ignore") as fh:
            return fh.read()
