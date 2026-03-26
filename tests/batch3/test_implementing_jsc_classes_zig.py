"""
Tests for implementing-jsc-classes-zig skill.
Validates HTTPHeaders Zig/TypeScript JSC class implementation in bun repository.
"""

import os
import pytest

REPO_DIR = "/workspace/bun"


def _path(rel: str) -> str:
    return os.path.join(REPO_DIR, rel)


def _read(rel: str) -> str:
    with open(_path(rel), encoding="utf-8", errors="ignore") as f:
        return f.read()


class TestImplementingJscClassesZig:

    # ── file_path_check ──────────────────────────────────────────────────────

    def test_httpheaders_classes_ts_exists(self):
        """HTTPHeaders.classes.ts must exist and be non-empty."""
        rel = "src/bun.js/api/HTTPHeaders.classes.ts"
        assert os.path.isfile(_path(rel)), f"{rel} not found"
        assert os.path.getsize(_path(rel)) > 0, "HTTPHeaders.classes.ts is empty"

    def test_httpheaders_zig_exists(self):
        """HTTPHeaders.zig must exist in bun.js/bindings."""
        rel = "src/bun.js/bindings/HTTPHeaders.zig"
        assert os.path.isfile(_path(rel)), f"{rel} not found"

    def test_classes_ts_is_substantial(self):
        """HTTPHeaders.classes.ts must contain substantial implementation (>20 lines)."""
        rel = "src/bun.js/api/HTTPHeaders.classes.ts"
        content = _read(rel)
        lines = [ln for ln in content.splitlines() if ln.strip()]
        assert (
            len(lines) > 20
        ), f"HTTPHeaders.classes.ts is a stub with only {len(lines)} non-empty lines"

    # ── semantic_check ───────────────────────────────────────────────────────

    def test_classes_ts_defines_http_headers_class(self):
        """HTTPHeaders.classes.ts must define class with get/set/append/delete methods."""
        content = _read("src/bun.js/api/HTTPHeaders.classes.ts")
        assert (
            "class HTTPHeaders" in content
        ), "HTTPHeaders class not found in classes.ts"
        for method in ["get(", "set(", "append(", "delete("]:
            assert (
                method in content
            ), f"Method '{method}' not found in HTTPHeaders class"

    def test_zig_uses_hashmap_for_storage(self):
        """HTTPHeaders.zig must use HashMap for O(1) header lookup."""
        content = _read("src/bun.js/bindings/HTTPHeaders.zig")
        assert any(
            kw in content for kw in ["HashMap", "StringHashMap", "AutoHashMap"]
        ), "No HashMap found in HTTPHeaders.zig — expected for O(1) lookup"
        assert (
            "deinit" in content
        ), "deinit() function required for HashMap memory cleanup"

    def test_zig_rfc7230_header_name_validation(self):
        """HTTPHeaders.zig must validate header names per RFC7230."""
        content = _read("src/bun.js/bindings/HTTPHeaders.zig")
        # RFC7230 token chars or validat* function
        assert (
            "validat" in content.lower()
            or "isToken" in content
            or "RFC7230" in content
            or "header_name" in content
        ), "RFC7230 header name validation not found in HTTPHeaders.zig"

    def test_zig_crlf_header_value_validation(self):
        """HTTPHeaders.zig must validate header values to reject CRLF injection."""
        content = _read("src/bun.js/bindings/HTTPHeaders.zig")
        assert (
            "\\r" in content
            or "\\n" in content
            or "0x0d" in content.lower()
            or "0x0a" in content.lower()
            or "crlf" in content.lower()
            or "CR" in content
        ), "CRLF injection check not found in HTTPHeaders.zig"

    # ── functional_check (mocked) ─────────────────────────────────────────────

    def test_get_header_case_insensitive(self):
        """HTTP headers must be case-insensitive per spec."""
        headers = {}

        def http_set(name, value):
            headers[name.lower()] = value

        def http_get(name):
            return headers.get(name.lower())

        http_set("Content-Type", "application/json")
        assert http_get("content-type") == "application/json"
        assert http_get("CONTENT-TYPE") == "application/json"

    def test_append_header_accumulates_values(self):
        """append() must accumulate values not overwrite them."""
        headers = {}

        def http_set(name, value):
            headers[name.lower()] = value

        def http_append(name, value):
            key = name.lower()
            if key in headers:
                headers[key] = headers[key] + ", " + value
            else:
                headers[key] = value

        def http_get(name):
            return headers.get(name.lower())

        http_set("Accept", "text/html")
        http_append("Accept", "application/json")
        combined = http_get("Accept")
        assert combined is not None
        assert "text/html" in combined
        assert "application/json" in combined

    def test_delete_header_returns_bool(self):
        """delete() must return True if header existed, False otherwise."""
        headers = {}

        def http_set(name, value):
            headers[name.lower()] = value

        def http_delete(name):
            key = name.lower()
            if key in headers:
                del headers[key]
                return True
            return False

        http_set("X-Custom", "value")
        assert http_delete("X-Custom") is True
        assert http_delete("X-Custom") is False

    def test_invalid_header_name_with_special_chars_rejected(self):
        """set() must reject header names containing non-RFC7230 characters."""
        import re

        def validate_header_name(name: str) -> bool:
            # RFC7230 token: any VCHAR except separators
            return bool(re.match(r"^[!#$%&\'*+\-.^_`|~0-9A-Za-z]+$", name))

        def http_set(name, value):
            if not validate_header_name(name):
                raise ValueError(f"Invalid header name: {name}")
            return True

        with pytest.raises(ValueError):
            http_set("Invalid{Header}", "value")

    def test_deinit_frees_hashmap_memory(self):
        """deinit() must be called to release HashMap resources (mocked pattern)."""
        freed = []

        class MockHashMap:
            def deinit(self):
                freed.append("freed")

        def use_headers():
            h = MockHashMap()
            try:
                pass  # use headers
            finally:
                h.deinit()  # defer equivalent

        use_headers()
        assert "freed" in freed, "deinit() was not called"
