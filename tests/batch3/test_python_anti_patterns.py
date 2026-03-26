"""
Tests for python-anti-patterns skill.
Validates LRU, LRI, and cachedproperty in boltons/cacheutils.py.
"""

import os
import pytest

REPO_DIR = "/workspace/boltons"


def _path(rel: str) -> str:
    return os.path.join(REPO_DIR, rel)


def _read(rel: str) -> str:
    with open(_path(rel), encoding="utf-8", errors="ignore") as f:
        return f.read()


class TestPythonAntiPatterns:

    # ── file_path_check ──────────────────────────────────────────────────────

    def test_cacheutils_file_exists(self):
        """boltons/cacheutils.py must exist."""
        rel = "boltons/cacheutils.py"
        assert os.path.isfile(_path(rel)), f"{rel} not found"
        assert os.path.getsize(_path(rel)) > 0, "cacheutils.py is empty"

    def test_boltons_package_init_exists(self):
        """boltons/__init__.py must exist for package importability."""
        rel = "boltons/__init__.py"
        assert os.path.isfile(_path(rel)), f"{rel} not found"

    # ── semantic_check ───────────────────────────────────────────────────────

    def test_lru_class_defined(self):
        """cacheutils.py must define LRU class with max_size parameter."""
        content = _read("boltons/cacheutils.py")
        assert "class LRU" in content, "LRU class not defined in cacheutils.py"
        assert "max_size" in content, "max_size parameter not found in cacheutils.py"

    def test_lri_class_defined(self):
        """cacheutils.py must define LRI class with on_miss parameter."""
        content = _read("boltons/cacheutils.py")
        assert "class LRI" in content, "LRI class not defined in cacheutils.py"
        assert "on_miss" in content, "on_miss parameter not found in cacheutils.py"

    def test_cachedproperty_is_descriptor(self):
        """cachedproperty must be a descriptor with __get__ method."""
        content = _read("boltons/cacheutils.py")
        assert "class cachedproperty" in content, "cachedproperty class not defined"
        assert "__get__" in content, "__get__ descriptor method not found"

    def test_lru_eviction_logic(self):
        """LRU must implement cache eviction when capacity is exceeded."""
        content = _read("boltons/cacheutils.py")
        has_eviction = (
            "popitem" in content
            or "pop(" in content
            or "OrderedDict" in content
            or "deque" in content
        )
        assert has_eviction, "No LRU eviction logic found in cacheutils.py"

    # ── functional_check ─────────────────────────────────────────────────────

    def test_lru_max_size_zero_raises_value_error(self):
        """LRU(max_size=0) must raise ValueError."""
        try:
            from boltons.cacheutils import LRU
        except ImportError:
            pytest.skip("boltons not installed")
        with pytest.raises(ValueError):
            LRU(max_size=0)

    def test_lru_capacity_5_after_10_inserts(self):
        """LRU(5) must contain exactly 5 entries after 10 insertions."""
        try:
            from boltons.cacheutils import LRU
        except ImportError:
            pytest.skip("boltons not installed")
        c = LRU(max_size=5)
        for i in range(10):
            c[i] = i
        assert len(c) == 5, f"Expected 5 entries, got {len(c)}"

    def test_lri_on_miss_non_callable_type_error(self):
        """LRI(on_miss='not_callable') must raise TypeError."""
        try:
            from boltons.cacheutils import LRI
        except ImportError:
            pytest.skip("boltons not installed")
        with pytest.raises(TypeError):
            LRI(on_miss="not_callable")

    def test_cachedproperty_class_access_is_descriptor(self):
        """Accessing cachedproperty via class __dict__ must return descriptor, not value."""
        try:
            from boltons.cacheutils import cachedproperty
        except ImportError:
            pytest.skip("boltons not installed")

        class MyClass:
            @cachedproperty
            def val(self):
                return 42

        result = MyClass.__dict__["val"]
        assert isinstance(
            result, cachedproperty
        ), f"Expected cachedproperty descriptor, got {type(result)}"

    def test_cachedproperty_cached_on_instance(self):
        """cachedproperty must compute value only once and cache in instance __dict__."""
        try:
            from boltons.cacheutils import cachedproperty
        except ImportError:
            pytest.skip("boltons not installed")

        call_count = [0]

        class MyClass:
            @cachedproperty
            def val(self):
                call_count[0] += 1
                return 42

        a = MyClass()
        _ = a.val
        _ = a.val
        assert (
            call_count[0] == 1
        ), f"cachedproperty computed {call_count[0]} times; expected exactly 1"

    def test_lru_unhashable_key_type_error(self):
        """Accessing LRU with unhashable key (list) must raise TypeError."""
        try:
            from boltons.cacheutils import LRU
        except ImportError:
            pytest.skip("boltons not installed")
        c = LRU(max_size=5)
        with pytest.raises(TypeError):
            _ = c[[1, 2, 3]]
