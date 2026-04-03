"""
Test for 'python-anti-patterns' skill — Resource Pool Module
Validates that the Agent created a thread-safe resource pool with
acquire/release, context manager, timeout, validation, and stats.
"""

import os
import re
import sys

import pytest


class TestPythonAntiPatterns:
    """Verify resource pool implementation (Python anti-patterns skill)."""

    REPO_DIR = "/workspace/boltons"

    @staticmethod
    def _read(path: str) -> str:
        try:
            with open(path, "r", errors="ignore") as fh:
                return fh.read()
        except OSError:
            return ""

    def _find_pool_module(self):
        for candidate in ("src/resource_pool/pool.py", "src/resource_pool.py"):
            path = os.path.join(self.REPO_DIR, candidate)
            if os.path.isfile(path):
                return path, candidate
        return None, None

    # ── file_path_check ─────────────────────────────────────────────

    def test_resource_pool_file_exists(self):
        """Verify resource_pool package or module file exists."""
        path, _ = self._find_pool_module()
        assert path is not None, "No resource_pool module found"

    def test_resource_pool_init_exists(self):
        """Verify package __init__.py or flat module exists."""
        found = (
            os.path.isfile(os.path.join(self.REPO_DIR, "src/resource_pool/__init__.py"))
            or os.path.isfile(os.path.join(self.REPO_DIR, "src/resource_pool.py"))
        )
        assert found, "Neither package __init__.py nor flat module found"

    # ── semantic_check ──────────────────────────────────────────────

    def test_resource_pool_class_api_defined(self):
        """Verify ResourcePool defines __init__, acquire, release, stats."""
        path, _ = self._find_pool_module()
        if path is None:
            pytest.skip("Pool module not found")
        content = self._read(path)
        for method in ("class ResourcePool", "def acquire", "def release", "def stats"):
            assert method in content, f"'{method}' not found in pool module"

    def test_thread_synchronization_mechanism(self):
        """Verify threading.Semaphore, Lock, or Queue used for thread safety."""
        path, _ = self._find_pool_module()
        if path is None:
            pytest.skip("Pool module not found")
        content = self._read(path)
        found = any(kw in content for kw in ("Semaphore", "threading.Lock", "Queue", "queue.Queue"))
        assert found, "No thread synchronization primitive found"

    def test_context_manager_protocol_implemented(self):
        """Verify __enter__/__exit__ or contextmanager decorator used."""
        path, _ = self._find_pool_module()
        if path is None:
            pytest.skip("Pool module not found")
        content = self._read(path)
        found = any(kw in content for kw in ("__enter__", "__exit__", "contextmanager"))
        assert found, "No context manager protocol found"

    # ── functional_check (import) ───────────────────────────────────

    def _import_pool(self):
        if not os.path.isdir(self.REPO_DIR):
            pytest.skip("Repo dir does not exist")
        sys.path.insert(0, os.path.join(self.REPO_DIR, "src"))
        try:
            from resource_pool.pool import ResourcePool
            return ResourcePool
        except ImportError:
            pytest.skip("resource_pool.pool not importable")
        finally:
            sys.path.pop(0)

    def test_acquire_returns_resource(self):
        """pool.acquire() returns a non-None resource."""
        ResourcePool = self._import_pool()
        pool = ResourcePool(factory=lambda: object(), max_size=2, timeout_seconds=1)
        r = pool.acquire()
        assert r is not None

    def test_release_increments_available(self):
        """After release, stats()['available'] equals 1 for max_size=1 pool."""
        ResourcePool = self._import_pool()
        pool = ResourcePool(factory=lambda: object(), max_size=1, timeout_seconds=1)
        r = pool.acquire()
        pool.release(r)
        assert pool.stats()["available"] == 1

    def test_context_manager_auto_releases(self):
        """Context manager auto-releases resource after with-block exits."""
        ResourcePool = self._import_pool()
        pool = ResourcePool(factory=lambda: object(), max_size=2, timeout_seconds=1)
        with pool.acquire() as r:
            in_use = pool.stats()["in_use"]
        avail_after = pool.stats()["available"]
        assert in_use == 1
        assert avail_after >= 1

    def test_timeout_error_on_full_pool(self):
        """Acquiring from full pool (max_size=1) raises TimeoutError."""
        ResourcePool = self._import_pool()
        pool = ResourcePool(factory=lambda: object(), max_size=1, timeout_seconds=0.05)
        r = pool.acquire()
        with pytest.raises(TimeoutError):
            pool.acquire()

    def test_invalid_resource_triggers_replacement(self):
        """validate_fn returning False causes total_created to exceed 1."""
        ResourcePool = self._import_pool()
        call_count = {"n": 0}

        def factory():
            call_count["n"] += 1
            return object()

        # validate_fn always False first time, True second
        calls = {"v": 0}
        def validate_fn(r):
            calls["v"] += 1
            return calls["v"] > 1

        pool = ResourcePool(factory=factory, max_size=2, timeout_seconds=1,
                           validate_fn=validate_fn)
        pool.acquire()
        assert pool.stats()["total_created"] > 1

    def test_stats_consistency_invariant(self):
        """stats()['available'] + stats()['in_use'] == stats()['total_created']."""
        ResourcePool = self._import_pool()
        pool = ResourcePool(factory=lambda: object(), max_size=3, timeout_seconds=1)
        r1 = pool.acquire()
        r2 = pool.acquire()
        s = pool.stats()
        assert s["available"] + s["in_use"] == s["total_created"]
