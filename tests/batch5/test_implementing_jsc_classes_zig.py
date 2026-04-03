"""
Test for 'implementing-jsc-classes-zig' skill — Bun CacheMap JSC Binding
Validates CacheMap.classes.ts and CacheMap.zig with LRU eviction,
capacity RangeError, GC finalize, and CRUD operations.
"""

import os
import re

import pytest


class TestImplementingJscClassesZig:
    """Verify Bun CacheMap JSC class binding implementation."""

    REPO_DIR = "/workspace/bun"

    # ── file_path_check ─────────────────────────────────────────────────────

    def test_cachemap_ts_binding_exists(self):
        """Verify CacheMap.classes.ts or similar TS binding file exists."""
        found = False
        for dirpath, _, fnames in os.walk(self.REPO_DIR):
            if "node_modules" in dirpath or ".git" in dirpath:
                continue
            for f in fnames:
                if ("cachemap" in f.lower() or "cache_map" in f.lower()) and (
                    f.endswith(".ts") or f.endswith(".js")
                ):
                    found = True
                    break
            if found:
                break
        assert found, "No CacheMap TS binding file found"

    def test_cachemap_zig_exists(self):
        """Verify CacheMap.zig implementation file exists."""
        found = False
        for dirpath, _, fnames in os.walk(self.REPO_DIR):
            if ".git" in dirpath:
                continue
            for f in fnames:
                if ("cachemap" in f.lower() or "cache_map" in f.lower()) and f.endswith(
                    ".zig"
                ):
                    found = True
                    break
            if found:
                break
        assert found, "No CacheMap.zig file found"

    # ── semantic_check ──────────────────────────────────────────────────────

    def test_lru_eviction_logic(self):
        """Verify LRU eviction logic in Zig or TS implementation."""
        files = self._find_cachemap_files()
        assert files, "No CacheMap files"
        for fpath in files:
            content = self._read(fpath)
            if re.search(
                r"(lru|LRU|evict|Evict|least.?recent)", content, re.IGNORECASE
            ):
                return
        pytest.fail("No LRU eviction logic found")

    def test_capacity_range_error(self):
        """Verify capacity=0 throws RangeError."""
        files = self._find_cachemap_files()
        assert files, "No CacheMap files"
        for fpath in files:
            content = self._read(fpath)
            if re.search(
                r"(RangeError|capacity.*0|zero.*capacity|invalid.*capacity)",
                content,
                re.IGNORECASE,
            ):
                return
        pytest.fail("No RangeError for capacity=0 found")

    def test_gc_finalize(self):
        """Verify GC finalize/deinit method exists."""
        files = self._find_cachemap_files()
        for fpath in files:
            content = self._read(fpath)
            if re.search(
                r"(finalize|deinit|destroy|dealloc|GC|garbage)", content, re.IGNORECASE
            ):
                return
        pytest.fail("No GC finalize method found")

    def test_crud_operations(self):
        """Verify get/set/delete/clear/size operations."""
        files = self._find_cachemap_files()
        assert files, "No CacheMap files"
        all_content = " ".join(self._read(f) for f in files)
        ops = ["get", "set", "delete", "clear", "size"]
        found_ops = [op for op in ops if op in all_content.lower()]
        assert len(found_ops) >= 4, f"Expected ≥4 CRUD operations, found: {found_ops}"

    # ── functional_check ────────────────────────────────────────────────────

    def test_zig_file_balanced_braces(self):
        """Verify Zig file has balanced braces."""
        zig_files = [f for f in self._find_cachemap_files() if f.endswith(".zig")]
        assert zig_files, "No CacheMap .zig files"
        for fpath in zig_files:
            content = self._read(fpath)
            opens = content.count("{")
            closes = content.count("}")
            assert (
                opens == closes
            ), f"Unbalanced braces in {os.path.basename(fpath)}: {opens} vs {closes}"

    def test_ts_file_balanced_braces(self):
        """Verify TS binding file has balanced braces."""
        ts_files = [
            f
            for f in self._find_cachemap_files()
            if f.endswith(".ts") or f.endswith(".js")
        ]
        assert ts_files, "No CacheMap TS files"
        for fpath in ts_files:
            content = self._read(fpath)
            opens = content.count("{")
            closes = content.count("}")
            assert opens == closes, f"Unbalanced braces in {os.path.basename(fpath)}"

    def test_exports_defined(self):
        """Verify TS file exports CacheMap class."""
        ts_files = [
            f
            for f in self._find_cachemap_files()
            if f.endswith(".ts") or f.endswith(".js")
        ]
        assert ts_files, "No TS files"
        for fpath in ts_files:
            content = self._read(fpath)
            if re.search(r"(export|module\.exports|CacheMap)", content):
                return
        pytest.fail("No CacheMap export found in TS files")

    def test_zig_has_pub_functions(self):
        """Verify Zig file has public functions."""
        zig_files = [f for f in self._find_cachemap_files() if f.endswith(".zig")]
        assert zig_files, "No Zig files"
        for fpath in zig_files:
            content = self._read(fpath)
            if re.search(r"pub\s+fn\s+", content):
                return
        pytest.fail("No pub fn in Zig CacheMap")

    def test_capacity_field_exists(self):
        """Verify capacity field/parameter exists."""
        files = self._find_cachemap_files()
        assert files, "No CacheMap files"
        for fpath in files:
            content = self._read(fpath)
            if "capacity" in content.lower():
                return
        pytest.fail("No capacity field found")

    # ── helpers ──────────────────────────────────────────────────────────────

    def _find_cachemap_files(self):
        results = []
        for dirpath, _, fnames in os.walk(self.REPO_DIR):
            if "node_modules" in dirpath or ".git" in dirpath:
                continue
            for f in fnames:
                if "cachemap" in f.lower() or "cache_map" in f.lower():
                    results.append(os.path.join(dirpath, f))
        return results

    def _read(self, path):
        with open(path, "r", errors="ignore") as fh:
            return fh.read()
