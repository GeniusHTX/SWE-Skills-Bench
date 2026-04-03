"""
Test for 'implementing-jsc-classes-zig' skill — JSC Classes in Bun (Zig)
Validates that the Agent generated URLPatternMatcher classes in Zig,
with proper .classes.ts definition and generated_classes_list.zig.
"""

import glob
import os
import re

import pytest


class TestImplementingJscClassesZig:
    """Verify JSC URLPatternMatcher class implementation in Bun."""

    REPO_DIR = "/workspace/bun"

    # ---- helpers ----

    @staticmethod
    def _read(path):
        with open(path, "r", errors="ignore") as fh:
            return fh.read()

    def _find_classes_ts(self):
        """Find URLPatternMatcher.classes.ts"""
        results = glob.glob(
            os.path.join(self.REPO_DIR, "**", "URLPatternMatcher.classes.ts"),
            recursive=True,
        )
        return results[0] if results else None

    def _find_zig_file(self):
        """Find the URLPatternMatcher .zig implementation."""
        results = glob.glob(
            os.path.join(self.REPO_DIR, "**", "URLPatternMatcher*.zig"),
            recursive=True,
        )
        return results[0] if results else None

    def _find_generated_list(self):
        """Find generated_classes_list.zig."""
        results = glob.glob(
            os.path.join(self.REPO_DIR, "**", "generated_classes_list.zig"),
            recursive=True,
        )
        return results[0] if results else None

    # ---- file_path_check ----

    def test_classes_ts_exists(self):
        """Verifies URLPatternMatcher.classes.ts exists."""
        path = self._find_classes_ts()
        assert path is not None, "URLPatternMatcher.classes.ts not found"

    def test_zig_impl_exists(self):
        """Verifies a .zig implementation file exists."""
        path = self._find_zig_file()
        assert path is not None, "URLPatternMatcher .zig file not found"

    def test_generated_classes_list_exists(self):
        """Verifies generated_classes_list.zig exists."""
        path = self._find_generated_list()
        assert path is not None, "generated_classes_list.zig not found"

    # ---- semantic_check ----

    def test_sem_class_name_in_ts(self):
        """Verifies 'URLPatternMatcher' referenced in .classes.ts."""
        content = self._read(self._find_classes_ts())
        assert (
            "URLPatternMatcher" in content
        ), "Class name 'URLPatternMatcher' not found in .classes.ts"

    def test_sem_match_method(self):
        """Verifies 'match' method defined in .classes.ts."""
        content = self._read(self._find_classes_ts())
        assert "match" in content, "'match' method not found in .classes.ts"

    def test_sem_test_method(self):
        """Verifies 'test' method defined in .classes.ts."""
        content = self._read(self._find_classes_ts())
        assert "test" in content, "'test' method not found in .classes.ts"

    def test_sem_pattern_property(self):
        """Verifies 'pattern' property defined in .classes.ts."""
        content = self._read(self._find_classes_ts())
        assert "pattern" in content, "'pattern' not found in .classes.ts"

    def test_sem_param_names(self):
        """Verifies 'paramNames' or 'param_names' used."""
        content = self._read(self._find_classes_ts())
        assert (
            "paramNames" in content or "param_names" in content
        ), "'paramNames' not found in .classes.ts"

    def test_sem_zig_struct(self):
        """Verifies .zig file defines a struct or class."""
        content = self._read(self._find_zig_file())
        assert (
            re.search(r"(pub\s+)?const\s+\w+\s*=\s*struct", content)
            or "struct" in content
        ), "No struct definition in .zig file"

    # ---- functional_check ----

    def test_func_named_params(self):
        """Verifies named parameter extraction (e.g., :id) in .classes.ts."""
        content = self._read(self._find_classes_ts())
        assert re.search(
            r"[:@]\w+|param|named|capture", content, re.IGNORECASE
        ), "No named parameter support in .classes.ts"

    def test_func_wildcards(self):
        """Verifies wildcard pattern support (* or glob)."""
        path = self._find_zig_file()
        content = self._read(path)
        assert (
            "*" in content or "wildcard" in content.lower() or "glob" in content.lower()
        ), "No wildcard support found in .zig file"

    def test_func_global_object(self):
        """Verifies globalObject or global_object referenced in .zig."""
        content = self._read(self._find_zig_file())
        assert (
            "globalObject" in content or "global_object" in content
        ), "No globalObject reference in .zig file"

    def test_func_throw_in_zig(self):
        """Verifies error throwing mechanism in .zig file."""
        content = self._read(self._find_zig_file())
        assert (
            "throw" in content.lower()
            or "error" in content.lower()
            or "return null" in content
        ), "No error/throw mechanism in .zig file"

    def test_func_consecutive_slashes(self):
        """Verifies handling of consecutive slashes in patterns."""
        content = self._read(self._find_zig_file())
        assert (
            "//" in content
            or "consecutive" in content.lower()
            or "normalize" in content.lower()
            or "slash" in content.lower()
        ), "No consecutive slash handling in .zig file"

    def test_func_argument_count(self):
        """Verifies argument count validation in .zig."""
        content = self._read(self._find_zig_file())
        assert re.search(
            r"args\.len|argument|arg_count|num_args", content, re.IGNORECASE
        ), "No argument count check in .zig file"

    def test_func_cached_property(self):
        """Verifies 'cached' or lazy property support."""
        ts_content = self._read(self._find_classes_ts())
        assert (
            "cache" in ts_content.lower() or "lazy" in ts_content.lower()
        ), "No cached property support in .classes.ts"
