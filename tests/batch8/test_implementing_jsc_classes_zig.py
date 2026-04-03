"""
Test for 'implementing-jsc-classes-zig' skill — Bun URLPattern JSC Binding
Validates that the Agent implemented a Zig-based JSC class binding for
URLPattern with constructor, test(), exec() methods and TypeScript interface.
"""

import os
import re

import pytest


class TestImplementingJscClassesZig:
    """Verify Bun URLPattern JSC Zig binding implementation."""

    REPO_DIR = "/workspace/bun"

    @staticmethod
    def _read(path: str) -> str:
        try:
            with open(path, "r", errors="ignore") as fh:
                return fh.read()
        except OSError:
            return ""

    # ── file_path_check ─────────────────────────────────────────────

    def test_urlpattern_zig_exists(self):
        """Verify URLPattern.zig binding file exists."""
        path = os.path.join(self.REPO_DIR, "src/bun.js/bindings/URLPattern.zig")
        assert os.path.isfile(path), "URLPattern.zig missing"

    def test_urlpattern_ts_interface_exists(self):
        """Verify URLPattern.ts TypeScript interface file exists under webcore."""
        path = os.path.join(self.REPO_DIR, "src/bun.js/webcore/URLPattern.ts")
        assert os.path.isfile(path), "URLPattern.ts missing"

    def test_urlpattern_test_file_exists(self):
        """Verify urlpattern.test.ts exists under test/js/web/ directory."""
        path = os.path.join(self.REPO_DIR, "test/js/web/urlpattern.test.ts")
        assert os.path.isfile(path), "urlpattern.test.ts missing"

    # ── semantic_check ──────────────────────────────────────────────

    def test_zig_exports_constructor_test_exec(self):
        """Verify URLPattern.zig exports constructor, test(), and exec() JSC methods."""
        content = self._read(os.path.join(
            self.REPO_DIR, "src/bun.js/bindings/URLPattern.zig"))
        assert content, "URLPattern.zig is empty or unreadable"
        for method in ("constructor", '"test"', '"exec"'):
            assert method in content, f"Method {method} not found in URLPattern.zig"

    def test_zig_uses_zig_string(self):
        """URLPattern.zig uses ZigString for JavaScript string interop."""
        content = self._read(os.path.join(
            self.REPO_DIR, "src/bun.js/bindings/URLPattern.zig"))
        assert content, "URLPattern.zig is empty or unreadable"
        assert "ZigString" in content, "ZigString not found in URLPattern.zig"

    def test_ts_exports_url_pattern_result_interface(self):
        """URLPattern.ts exports URLPatternResult TypeScript interface."""
        content = self._read(os.path.join(
            self.REPO_DIR, "src/bun.js/webcore/URLPattern.ts"))
        assert content, "URLPattern.ts is empty or unreadable"
        assert "URLPatternResult" in content, "URLPatternResult interface not found"
        assert "interface" in content, "No interface keyword in URLPattern.ts"

    def test_zig_class_decorator_present(self):
        """Verify JSC class decorator or pub const class definition is present."""
        content = self._read(os.path.join(
            self.REPO_DIR, "src/bun.js/bindings/URLPattern.zig"))
        assert content, "URLPattern.zig is empty or unreadable"
        found = any(kw in content for kw in ("pub const", "@export", "JSC.implement"))
        assert found, "No JSC class export pattern found in URLPattern.zig"

    def test_test_file_covers_exec_and_test_methods(self):
        """urlpattern.test.ts includes test cases for both .test() and .exec() methods."""
        content = self._read(os.path.join(
            self.REPO_DIR, "test/js/web/urlpattern.test.ts"))
        assert content, "urlpattern.test.ts is empty or unreadable"
        assert ".test(" in content, ".test() not covered in test file"
        assert ".exec(" in content, ".exec() not covered in test file"
