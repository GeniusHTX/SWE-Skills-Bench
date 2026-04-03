"""
Test for 'python-anti-patterns' skill — Python Anti-Pattern Refactoring
Validates refactored boltons library code for absence of common anti-patterns:
mutable default arguments, bare except clauses, builtin shadowing, and verifies
correct LRU eviction, chunked iteration, slugify, and __slots__ usage.
"""

import glob
import os
import re
import sys

import pytest


class TestPythonAntiPatterns:
    """Verify Python anti-pattern fixes in the boltons library."""

    REPO_DIR = "/workspace/boltons"

    # ── helpers ──────────────────────────────────────────────────────────

    @staticmethod
    def _read_file(path: str) -> str:
        try:
            with open(path, "r", errors="ignore") as fh:
                return fh.read()
        except OSError:
            return ""

    def _boltons_path(self, name: str) -> str:
        return os.path.join(self.REPO_DIR, "boltons", name)

    def _install_boltons(self):
        """Install boltons in editable mode if not already importable."""
        try:
            import boltons
        except ImportError:
            import subprocess
            result = subprocess.run(
                [sys.executable, "-m", "pip", "install", "-e", "."],
                cwd=self.REPO_DIR,
                capture_output=True,
                timeout=60,
            )
            if result.returncode != 0:
                pytest.skip(f"pip install -e . failed: {result.stderr[:200]}")

    # ── file_path_check ──────────────────────────────────────────────────

    def test_cacheutils_py_exists(self):
        """boltons/cacheutils.py must exist with LRU/LRI cache implementations."""
        path = self._boltons_path("cacheutils.py")
        assert os.path.isfile(path), f"{path} does not exist"
        assert os.path.getsize(path) > 0

    def test_iterutils_and_strutils_exist(self):
        """boltons/iterutils.py and boltons/strutils.py must exist."""
        for name in ("iterutils.py", "strutils.py"):
            path = self._boltons_path(name)
            assert os.path.isfile(path), f"{path} does not exist"
            assert os.path.getsize(path) > 0

    def test_dictutils_and_test_file_exist(self):
        """boltons/dictutils.py and tests/test_refactored_anti_patterns.py must exist."""
        dict_path = self._boltons_path("dictutils.py")
        assert os.path.isfile(dict_path), f"{dict_path} does not exist"
        test_path = os.path.join(self.REPO_DIR, "tests", "test_refactored_anti_patterns.py")
        assert os.path.isfile(test_path), f"{test_path} does not exist"

    # ── semantic_check ───────────────────────────────────────────────────

    def test_no_mutable_default_arguments(self):
        """No mutable defaults ([], {}, set()) in function signatures."""
        files = ["cacheutils.py", "iterutils.py", "strutils.py", "dictutils.py"]
        pattern = re.compile(r"def\s+\w+\(.*=\s*(\[\]|\{\}|set\(\))", re.MULTILINE)
        for name in files:
            path = self._boltons_path(name)
            if not os.path.isfile(path):
                continue
            content = self._read_file(path)
            match = pattern.search(content)
            assert match is None, f"Mutable default argument found in {name}: {match.group()}"

    def test_no_bare_except_clauses(self):
        """No bare 'except:' clauses in any boltons file."""
        files = ["cacheutils.py", "iterutils.py", "strutils.py", "dictutils.py"]
        bare_except = re.compile(r"^\s*except\s*:\s*$", re.MULTILINE)
        for name in files:
            path = self._boltons_path(name)
            if not os.path.isfile(path):
                continue
            content = self._read_file(path)
            match = bare_except.search(content)
            assert match is None, f"Bare except clause found in {name}"

    def test_no_builtin_shadowing_in_iterutils(self):
        """iterutils.py must not shadow builtins: input, list, type, dict, id, map, filter."""
        path = self._boltons_path("iterutils.py")
        if not os.path.isfile(path):
            pytest.skip("iterutils.py not found")
        content = self._read_file(path)
        builtins_to_check = ["input", "list", "type", "dict", "id", "map", "filter"]
        for name in builtins_to_check:
            pattern = re.compile(rf"^\s+{name}\s*=\s*", re.MULTILINE)
            match = pattern.search(content)
            if match:
                # Allow it if it's clearly a parameter or property, not a standalone assignment
                line = match.group().strip()
                if not line.startswith("self."):
                    assert False, f"Builtin '{name}' appears shadowed in iterutils.py: {line}"

    def test_lru_link_uses_slots(self):
        """LRU inner class (_Link/_Node) must use __slots__ for memory efficiency."""
        path = self._boltons_path("cacheutils.py")
        if not os.path.isfile(path):
            pytest.skip("cacheutils.py not found")
        content = self._read_file(path)
        assert "__slots__" in content, "__slots__ not found in cacheutils.py"

    def test_string_building_uses_join(self):
        """strutils.py should use str.join() not += concatenation in loops."""
        path = self._boltons_path("strutils.py")
        if not os.path.isfile(path):
            pytest.skip("strutils.py not found")
        content = self._read_file(path)
        assert "join(" in content, "str.join() not found in strutils.py"

    # ── functional_check ─────────────────────────────────────────────────

    def test_lru_eviction_removes_least_recently_used(self):
        """LRU(max_size=3) with 4 insertions must evict the earliest key."""
        self._install_boltons()
        try:
            from boltons.cacheutils import LRU
        except ImportError:
            pytest.skip("Cannot import LRU from boltons.cacheutils")
        lru = LRU(max_size=3)
        lru["a"] = 1
        lru["b"] = 2
        lru["c"] = 3
        lru["d"] = 4
        assert "a" not in lru, "'a' should have been evicted"
        assert "d" in lru, "'d' should be present"

    def test_chunked_splits_list(self):
        """chunked([1,2,3,4,5], 2) must return [[1,2],[3,4],[5]]."""
        self._install_boltons()
        try:
            from boltons.iterutils import chunked
        except ImportError:
            pytest.skip("Cannot import chunked from boltons.iterutils")
        result = chunked([1, 2, 3, 4, 5], 2)
        assert result == [[1, 2], [3, 4], [5]]

    def test_mutable_default_double_call_isolation(self):
        """Functions with fixed mutable defaults must not accumulate state."""
        self._install_boltons()
        try:
            from boltons.iterutils import chunked
        except ImportError:
            pytest.skip("Cannot import chunked from boltons.iterutils")
        r1 = chunked([1, 2, 3], 2)
        r2 = chunked([1, 2, 3], 2)
        assert r1 == r2, "Repeated calls should return identical results (no state leakage)"

    def test_slugify_converts_special_chars(self):
        """slugify('Hello World!') must return a lowercase slug with no special chars."""
        self._install_boltons()
        try:
            from boltons.strutils import slugify
        except ImportError:
            pytest.skip("Cannot import slugify from boltons.strutils")
        result = slugify("Hello World!")
        assert result == result.lower(), "slug must be lowercase"
        assert " " not in result, "slug must not contain spaces"
        assert "!" not in result, "slug must not contain exclamation marks"

    def test_lru_access_updates_recency_order(self):
        """Accessing an existing LRU key must update recency, preventing eviction."""
        self._install_boltons()
        try:
            from boltons.cacheutils import LRU
        except ImportError:
            pytest.skip("Cannot import LRU from boltons.cacheutils")
        lru = LRU(max_size=3)
        lru["a"] = 1
        lru["b"] = 2
        lru["c"] = 3
        _ = lru["a"]  # access 'a' to make it recently used
        lru["d"] = 4  # should evict 'b' not 'a'
        assert "b" not in lru, "'b' should have been evicted"
        assert "a" in lru, "'a' should remain (was recently accessed)"
        assert "d" in lru, "'d' should be present"
