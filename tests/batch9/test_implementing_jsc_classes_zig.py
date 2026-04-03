"""
Test for 'implementing-jsc-classes-zig' skill — Bun JSC Duration Class in Zig
Validates Duration.classes.ts TypeScript binding definition, Duration.zig struct fields,
ISO 8601 parser, finalize/destroy, codegen registration, and error handling.
"""

import glob
import os
import re

import pytest


class TestImplementingJscClassesZig:
    """Verify Bun JSC Duration class implementation in Zig and TypeScript."""

    REPO_DIR = "/workspace/bun"

    # ── helpers ──────────────────────────────────────────────────────────

    @staticmethod
    def _read_file(path: str) -> str:
        try:
            with open(path, "r", errors="ignore") as fh:
                return fh.read()
        except OSError:
            return ""

    def _api_path(self, name: str) -> str:
        return os.path.join(self.REPO_DIR, "src", "bun.js", "api", name)

    def _bindings_path(self, name: str) -> str:
        return os.path.join(self.REPO_DIR, "src", "bun.js", "bindings", name)

    # ── file_path_check ──────────────────────────────────────────────────

    def test_duration_classes_ts_exists(self):
        """Duration.classes.ts must exist as the TypeScript class binding definition."""
        path = self._api_path("Duration.classes.ts")
        assert os.path.isfile(path), f"{path} does not exist"
        assert os.path.getsize(path) > 0

    def test_duration_zig_exists(self):
        """Duration.zig must exist with ISO parser and arithmetic."""
        path = self._api_path("Duration.zig")
        assert os.path.isfile(path), f"{path} does not exist"
        assert os.path.getsize(path) > 0

    def test_generated_classes_list_contains_duration(self):
        """generated_classes_list.zig must contain a Duration entry."""
        path = self._bindings_path("generated_classes_list.zig")
        assert os.path.isfile(path), f"{path} does not exist"
        content = self._read_file(path)
        assert "Duration" in content, "Duration not registered in generated_classes_list.zig"

    def test_duration_test_file_exists(self):
        """test/js/bun/duration.test.ts must exist."""
        path = os.path.join(self.REPO_DIR, "test", "js", "bun", "duration.test.ts")
        assert os.path.isfile(path), f"{path} does not exist"

    # ── semantic_check ───────────────────────────────────────────────────

    def test_classes_ts_define_has_all_proto_methods(self):
        """Duration.classes.ts define() must include all 7 proto methods."""
        path = self._api_path("Duration.classes.ts")
        if not os.path.isfile(path):
            pytest.skip("Duration.classes.ts not found")
        content = self._read_file(path)
        assert "define(" in content, "define() call not found"
        required_methods = ["add", "subtract", "multiply", "toSeconds", "toISO", "toString", "compare"]
        for method in required_methods:
            assert method in content, f"Proto method '{method}' not found in Duration.classes.ts"

    def test_classes_ts_property_getters_with_cache(self):
        """Duration.classes.ts must have 6 cached property getters."""
        path = self._api_path("Duration.classes.ts")
        if not os.path.isfile(path):
            pytest.skip("Duration.classes.ts not found")
        content = self._read_file(path)
        properties = ["years", "months", "days", "hours", "minutes", "seconds"]
        for prop in properties:
            assert prop in content, f"Property getter '{prop}' not found"
        assert "cache" in content.lower(), "cache attribute not found in getters"

    def test_zig_struct_has_required_fields(self):
        """Duration.zig struct must declare i32 integer fields and f64 seconds."""
        path = self._api_path("Duration.zig")
        if not os.path.isfile(path):
            pytest.skip("Duration.zig not found")
        content = self._read_file(path)
        int_fields = ["years", "months", "days", "hours", "minutes"]
        for field in int_fields:
            assert field in content, f"Field '{field}' not found in Duration.zig"
        assert "i32" in content, "i32 type not found in Duration.zig for integer fields"
        assert "seconds" in content, "seconds field not found"
        assert "f64" in content, "f64 type not found for seconds field"

    def test_zig_finalize_calls_destroy(self):
        """Duration.zig must have finalize() calling bun.destroy for memory management."""
        path = self._api_path("Duration.zig")
        if not os.path.isfile(path):
            pytest.skip("Duration.zig not found")
        content = self._read_file(path)
        assert "finalize" in content, "finalize function not defined in Duration.zig"
        assert "destroy" in content, "destroy call not found in Duration.zig"

    def test_zig_handles_invalid_duration_error(self):
        """Duration.zig must throw JSError for invalid ISO 8601 duration strings."""
        path = self._api_path("Duration.zig")
        if not os.path.isfile(path):
            pytest.skip("Duration.zig not found")
        content = self._read_file(path)
        has_error = (
            "invalid" in content.lower()
            or "Invalid duration" in content
            or "JSError" in content
            or "throwError" in content
        )
        assert has_error, "No error handling for invalid duration format found"

    # ── functional_check (static source inspection) ──────────────────────

    def test_iso_parser_handles_all_components(self):
        """ISO 8601 parser must handle P, Y, M, D, T, H, M, S designators."""
        path = self._api_path("Duration.zig")
        if not os.path.isfile(path):
            pytest.skip("Duration.zig not found")
        content = self._read_file(path)
        designators = ["'Y'", "'M'", "'D'", "'T'", "'H'", "'S'"]
        found_count = sum(1 for d in designators if d in content)
        assert found_count >= 5, \
            f"Only {found_count}/6 ISO designator characters found in parser"

    def test_iso_parser_handles_fractional_seconds(self):
        """Parser must use parseFloat or equivalent for fractional seconds like PT6.5S."""
        path = self._api_path("Duration.zig")
        if not os.path.isfile(path):
            pytest.skip("Duration.zig not found")
        content = self._read_file(path)
        has_float_parse = "parseFloat" in content or "std.fmt.parseFloat" in content
        assert has_float_parse, "No float parsing found for fractional seconds"

    def test_zig_codegen_jsduration_declared(self):
        """Duration.zig must declare pub const js = JSC.Codegen.JSDuration."""
        path = self._api_path("Duration.zig")
        if not os.path.isfile(path):
            pytest.skip("Duration.zig not found")
        content = self._read_file(path)
        assert "JSC.Codegen.JSDuration" in content or "Codegen.JsDuration" in content, \
            "JSC.Codegen.JSDuration binding declaration not found"
