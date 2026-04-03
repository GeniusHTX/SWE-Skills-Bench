"""Test file for the implementing-jsc-classes-zig skill.

This suite validates the RingBuffer JSC binding files and runtime behavior
expected in the bun repository.
"""

from __future__ import annotations

import json
import pathlib
import re
import shutil
import subprocess
import tempfile
import textwrap

import pytest


class TestImplementingJscClassesZig:
    """Verify the RingBuffer JSC binding implementation."""

    REPO_DIR = "/workspace/bun"

    def _repo_path(self, relative_path: str) -> pathlib.Path:
        return pathlib.Path(self.REPO_DIR, *relative_path.split("/"))

    def _read_text(self, relative_path: str) -> str:
        path = self._repo_path(relative_path)
        assert path.exists(), f"Expected path to exist: {path}"
        return path.read_text(encoding="utf-8", errors="ignore")

    def _assert_non_empty_file(self, relative_path: str) -> pathlib.Path:
        path = self._repo_path(relative_path)
        assert path.is_file(), f"Expected file to exist: {path}"
        assert path.stat().st_size > 0, f"Expected file to be non-empty: {path}"
        return path

    def _window_after(self, text: str, anchors: list[str], size: int = 1800) -> str:
        for anchor in anchors:
            index = text.find(anchor)
            if index >= 0:
                return text[index : index + size]
        pytest.fail(f"Could not find any anchor from: {anchors}")

    def _find_bun_binary(self) -> str:
        repo = pathlib.Path(self.REPO_DIR)
        candidates = [
            repo / "build" / "release" / "bun",
            repo / "build" / "debug" / "bun",
            repo / "build" / "bun-release" / "bun",
            repo / "build" / "bun-debug" / "bun",
            repo / ".build" / "release" / "bun",
            repo / ".build" / "debug" / "bun",
            repo / "bun",
        ]
        for candidate in candidates:
            if candidate.exists() and candidate.is_file():
                return str(candidate)
        system_bun = shutil.which("bun")
        assert system_bun, "Could not locate a bun binary in the repository or on PATH"
        return system_bun

    def _run_bun_json(self, source: str, timeout: int = 120) -> dict:
        bun_binary = self._find_bun_binary()
        with tempfile.NamedTemporaryFile(
            "w", suffix=".js", delete=False, encoding="utf-8"
        ) as handle:
            handle.write(source)
            temp_path = pathlib.Path(handle.name)
        try:
            result = subprocess.run(
                [bun_binary, str(temp_path)],
                cwd=self.REPO_DIR,
                capture_output=True,
                text=True,
                timeout=timeout,
            )
        finally:
            temp_path.unlink(missing_ok=True)
        assert result.returncode == 0, (
            "Expected bun script to succeed.\n"
            f"stdout:\n{result.stdout}\n"
            f"stderr:\n{result.stderr}"
        )
        stdout = result.stdout.strip()
        assert stdout, "Expected bun script to emit JSON output"
        return json.loads(stdout)

    def test_file_path_src_bun_js_api_ringbuffer_classes_ts_exists(self) -> None:
        """Verify that RingBuffer.classes.ts exists at the expected path and is non-empty."""
        self._assert_non_empty_file("src/bun.js/api/RingBuffer.classes.ts")

    def test_file_path_src_bun_js_api_ringbuffer_zig_exists(self) -> None:
        """Verify that RingBuffer.zig exists at the expected path and is non-empty."""
        self._assert_non_empty_file("src/bun.js/api/RingBuffer.zig")

    def test_file_path_src_bun_js_bindings_generated_classes_list_zig_modified_to_i(
        self,
    ) -> None:
        """Verify that generated_classes_list.zig exists and includes RingBuffer in the generated class list."""
        path = self._assert_non_empty_file(
            "src/bun.js/bindings/generated_classes_list.zig"
        )
        content = path.read_text(encoding="utf-8", errors="ignore")
        assert re.search(
            r"\bRingBuffer\b", content
        ), "Expected generated class list to include RingBuffer"

    def test_semantic_ringbuffer_classes_ts_defines_constructor_properties_and_met(
        self,
    ) -> None:
        """Verify that RingBuffer.classes.ts declares constructor support, core methods, and exposed properties."""
        content = self._read_text("src/bun.js/api/RingBuffer.classes.ts")
        constructor_patterns = [
            r"\bconstructor\b",
            r"\bconstruct(?:or|able)?\b",
            r"new\s+RingBuffer",
        ]
        method_names = set(re.findall(r"\b(write|read|peek|toBytes)\b", content))
        property_names = set(
            re.findall(r"\b(length|capacity|available|isEmpty|isFull)\b", content)
        )
        assert any(
            re.search(pattern, content) for pattern in constructor_patterns
        ), "Expected RingBuffer.classes.ts to define a constructor entry"
        assert method_names == {
            "write",
            "read",
            "peek",
            "toBytes",
        }, f"Expected write/read/peek/toBytes methods, got: {sorted(method_names)}"
        assert property_names == {
            "available",
            "capacity",
            "isEmpty",
            "isFull",
            "length",
        }, f"Expected all RingBuffer properties to be exposed, got: {sorted(property_names)}"

    def test_semantic_ringbuffer_zig_uses_bun_default_allocator_for_buffer_allocat(
        self,
    ) -> None:
        """Verify that RingBuffer.zig allocates and releases its buffer through bun.default_allocator."""
        content = self._read_text("src/bun.js/api/RingBuffer.zig")
        assert re.search(
            r"\bbun\.default_allocator\b", content
        ), "Expected RingBuffer.zig to reference bun.default_allocator"
        assert re.search(
            r"\b(?:alloc|create)\b", content
        ), "Expected RingBuffer.zig to allocate backing storage"
        assert re.search(
            r"\b(?:free|destroy)\b", content
        ), "Expected RingBuffer.zig to release backing storage"

    def test_semantic_ringbuffer_zig_implements_head_tail_pointer_design(self) -> None:
        """Verify that RingBuffer.zig uses explicit head and tail state with wrap-around arithmetic."""
        content = self._read_text("src/bun.js/api/RingBuffer.zig")
        fields = set(re.findall(r"\b(head|tail|capacity|length)\b", content))
        assert {"head", "tail", "capacity"}.issubset(
            fields
        ), f"Expected head/tail/capacity state fields, got: {sorted(fields)}"
        assert re.search(
            r"(?:@mod|%|%=)", content
        ), "Expected wrap-around arithmetic in RingBuffer implementation"

    def test_semantic_write_method_handles_two_segment_memcpy_for_wrap_around(
        self,
    ) -> None:
        """Verify that the write path performs split copy logic when data wraps around the end of the buffer."""
        content = self._read_text("src/bun.js/api/RingBuffer.zig")
        write_window = self._window_after(
            content, ["fn write", "pub fn write", "write("]
        )
        copy_count = len(
            re.findall(r"(?:memcpy|copyForwards|copyBackwards|copy)", write_window)
        )
        assert (
            copy_count >= 2
        ), "Expected the write implementation to perform at least two copy operations for wrap-around handling"
        assert re.search(
            r"(?:remaining|first|second|split|tail|head)", write_window
        ), "Expected the write implementation to track split copy segments"

    def test_semantic_read_method_handles_two_segment_memcpy_for_wrap_around(
        self,
    ) -> None:
        """Verify that the read path performs split copy logic when buffered data wraps around."""
        content = self._read_text("src/bun.js/api/RingBuffer.zig")
        read_window = self._window_after(content, ["fn read", "pub fn read", "read("])
        copy_count = len(
            re.findall(r"(?:memcpy|copyForwards|copyBackwards|copy)", read_window)
        )
        assert (
            copy_count >= 2
        ), "Expected the read implementation to perform at least two copy operations for wrap-around handling"
        assert re.search(
            r"(?:remaining|first|second|split|tail|head)", read_window
        ), "Expected the read implementation to track split copy segments"

    def test_functional_new_ringbuffer_8_creates_8_byte_capacity_buffer(self) -> None:
        """Verify that a freshly constructed RingBuffer(8) reports the expected empty-buffer state."""
        payload = self._run_bun_json(
            textwrap.dedent(
                """
                const rb = new RingBuffer(8);
                console.log(JSON.stringify({
                  capacity: rb.capacity,
                  length: rb.length,
                  available: rb.available,
                  isEmpty: rb.isEmpty,
                  isFull: rb.isFull,
                }));
                """
            )
        )
        assert payload["capacity"] == 8, payload
        assert payload["length"] == 0, payload
        assert payload["available"] == 8, payload
        assert payload["isEmpty"] is True, payload
        assert payload["isFull"] is False, payload

    def test_functional_write_1_2_3_4_5_to_8_capacity_length_5_available_3(
        self,
    ) -> None:
        """Verify that writing five bytes returns the written count and updates the buffer accounting fields."""
        payload = self._run_bun_json(
            textwrap.dedent(
                """
                const rb = new RingBuffer(8);
                const written = rb.write(new Uint8Array([1, 2, 3, 4, 5]));
                console.log(JSON.stringify({
                  written,
                  length: rb.length,
                  available: rb.available,
                  isEmpty: rb.isEmpty,
                  isFull: rb.isFull,
                }));
                """
            )
        )
        assert payload["written"] == 5, payload
        assert payload["length"] == 5, payload
        assert payload["available"] == 3, payload
        assert payload["isEmpty"] is False, payload
        assert payload["isFull"] is False, payload

    def test_functional_read_3_bytes_returns_1_2_3_length_2(self) -> None:
        """Verify that reading three bytes returns the correct prefix and leaves the remaining length intact."""
        payload = self._run_bun_json(
            textwrap.dedent(
                """
                const rb = new RingBuffer(8);
                rb.write(new Uint8Array([1, 2, 3, 4, 5]));
                const readBack = Array.from(rb.read(3));
                console.log(JSON.stringify({
                  readBack,
                  length: rb.length,
                  available: rb.available,
                }));
                """
            )
        )
        assert payload["readBack"] == [1, 2, 3], payload
        assert payload["length"] == 2, payload
        assert payload["available"] == 6, payload

    def test_functional_write_exceeding_available_space_returns_partial_write_count(
        self,
    ) -> None:
        """Verify that writing past the remaining capacity reports a partial write and leaves the buffer full."""
        payload = self._run_bun_json(
            textwrap.dedent(
                """
                const rb = new RingBuffer(8);
                const first = rb.write(new Uint8Array([1, 2, 3, 4, 5]));
                const second = rb.write(new Uint8Array([6, 7, 8, 9]));
                console.log(JSON.stringify({
                  first,
                  second,
                  length: rb.length,
                  available: rb.available,
                  isFull: rb.isFull,
                  bytes: Array.from(rb.toBytes()),
                }));
                """
            )
        )
        assert payload["first"] == 5, payload
        assert payload["second"] == 3, payload
        assert payload["length"] == 8, payload
        assert payload["available"] == 0, payload
        assert payload["isFull"] is True, payload
        assert payload["bytes"] == [1, 2, 3, 4, 5, 6, 7, 8], payload

    def test_functional_peek_does_not_change_length_or_read_position(self) -> None:
        """Verify that peek returns bytes without consuming them and preserves the subsequent read order."""
        payload = self._run_bun_json(
            textwrap.dedent(
                """
                const rb = new RingBuffer(8);
                rb.write(new Uint8Array([1, 2, 3, 4]));
                const peeked = Array.from(rb.peek(2));
                const lengthAfterPeek = rb.length;
                const readBack = Array.from(rb.read(2));
                console.log(JSON.stringify({
                  peeked,
                  lengthAfterPeek,
                  readBack,
                  finalLength: rb.length,
                }));
                """
            )
        )
        assert payload["peeked"] == [1, 2], payload
        assert payload["lengthAfterPeek"] == 4, payload
        assert payload["readBack"] == [1, 2], payload
        assert payload["finalLength"] == 2, payload
