"""
Test for 'add-uint-support' skill — PyTorch Unsigned Integer Support
Validates CUDA kernels for uint32/uint64 in bitwise, shift, and minmax operations.
"""

import os
import re
import subprocess

import pytest


class TestAddUintSupport:
    """Verify PyTorch unsigned integer CUDA kernel support."""

    REPO_DIR = "/workspace/pytorch"

    # ── file_path_check ─────────────────────────────────────────────────────

    def test_cuda_kernel_files_exist(self):
        """Verify CUDA kernel .cu files exist for bitwise, shift, and minmax."""
        aten_dir = os.path.join(self.REPO_DIR, "aten", "src", "ATen", "native", "cuda")
        if not os.path.isdir(aten_dir):
            pytest.skip("ATen CUDA native directory not found")
        cu_files = [f for f in os.listdir(aten_dir) if f.endswith(".cu")]
        keywords = ["bitwise", "shift", "max", "min"]
        matches = [f for f in cu_files if any(k in f.lower() for k in keywords)]
        assert (
            len(matches) >= 2
        ), f"Expected ≥2 CUDA kernel files for bitwise/shift/minmax, found: {matches}"

    def test_dispatch_header_exists(self):
        """Verify AT_DISPATCH macros header or dispatch files exist."""
        found = False
        for dirpath, _, fnames in os.walk(os.path.join(self.REPO_DIR, "aten")):
            for f in fnames:
                if "dispatch" in f.lower() and (f.endswith(".h") or f.endswith(".cu")):
                    found = True
                    break
            if found:
                break
        assert found, "No dispatch header/file found in aten/"

    # ── semantic_check ──────────────────────────────────────────────────────

    def test_at_dispatch_macro_includes_uint(self):
        """Verify AT_DISPATCH macro call includes uint32 or uint64 types."""
        cu_files = self._find_cu_files(["bitwise", "shift", "max", "min"])
        assert cu_files, "No relevant CUDA kernel files found"
        found_uint = False
        for fpath in cu_files:
            content = self._read(fpath)
            if re.search(
                r"uint32|uint64|kUInt32|kUInt64|AT_DISPATCH.*uint",
                content,
                re.IGNORECASE,
            ):
                found_uint = True
                break
        assert found_uint, "No CUDA kernel dispatches uint32/uint64 types"

    def test_bitwise_kernel_dispatches_uint(self):
        """Verify the bitwise kernel specifically dispatches unsigned types."""
        cu_files = self._find_cu_files(["bitwise"])
        if not cu_files:
            pytest.skip("No bitwise CUDA kernel file found")
        content = self._read(cu_files[0])
        assert re.search(
            r"uint|unsigned", content, re.IGNORECASE
        ), "Bitwise kernel does not reference unsigned types"

    def test_shift_kernel_dispatches_uint(self):
        """Verify the shift kernel dispatches unsigned types."""
        cu_files = self._find_cu_files(["shift"])
        if not cu_files:
            pytest.skip("No shift CUDA kernel file found")
        content = self._read(cu_files[0])
        assert re.search(
            r"uint|unsigned", content, re.IGNORECASE
        ), "Shift kernel does not reference unsigned types"

    def test_signed_types_preserved(self):
        """Verify existing signed type dispatches are not removed."""
        cu_files = self._find_cu_files(["bitwise", "shift", "max", "min"])
        assert cu_files, "No relevant kernel files"
        for fpath in cu_files:
            content = self._read(fpath)
            if re.search(r"int32|int64|kInt|kLong|AT_DISPATCH_ALL_TYPES", content):
                return  # pass – signed types still present
        pytest.fail("No kernel file preserves standard signed type dispatch")

    # ── functional_check ────────────────────────────────────────────────────

    def test_cuda_files_compile_syntax(self):
        """Verify each CUDA file has balanced braces (basic syntax check)."""
        cu_files = self._find_cu_files(["bitwise", "shift", "max", "min"])
        assert cu_files, "No kernel files found"
        for fpath in cu_files:
            content = self._read(fpath)
            opens = content.count("{")
            closes = content.count("}")
            assert opens == closes, f"Unbalanced braces in {os.path.basename(fpath)}"

    def test_maxmin_kernel_has_uint_support(self):
        """Verify maxmin kernel handles unsigned types."""
        cu_files = self._find_cu_files(["max", "min"])
        if not cu_files:
            pytest.skip("No minmax CUDA kernel files found")
        content = self._read(cu_files[0])
        assert re.search(
            r"uint|unsigned", content, re.IGNORECASE
        ), "Max/min kernel missing uint support"

    def test_kernel_files_include_required_headers(self):
        """Verify CUDA kernel files include ATen headers."""
        cu_files = self._find_cu_files(["bitwise", "shift", "max", "min"])
        assert cu_files, "No kernel files"
        for fpath in cu_files:
            content = self._read(fpath)
            if "#include" in content and "ATen" in content:
                return  # pass
        pytest.fail("No kernel file includes ATen headers")

    def test_no_duplicate_dispatch_entries(self):
        """Verify AT_DISPATCH calls do not list the same type twice."""
        cu_files = self._find_cu_files(["bitwise", "shift", "max", "min"])
        assert cu_files, "No kernel files"
        for fpath in cu_files:
            content = self._read(fpath)
            for m in re.finditer(r"AT_DISPATCH\w+\(([^)]+)\)", content):
                types_str = m.group(1)
                tokens = re.findall(r"\b(k\w+)\b", types_str)
                assert len(tokens) == len(
                    set(tokens)
                ), f"Duplicate type in dispatch macro in {os.path.basename(fpath)}"

    # ── helpers ──────────────────────────────────────────────────────────────

    def _find_cu_files(self, keywords):
        aten_dir = os.path.join(self.REPO_DIR, "aten", "src", "ATen", "native", "cuda")
        if not os.path.isdir(aten_dir):
            return []
        results = []
        for f in os.listdir(aten_dir):
            if f.endswith(".cu") and any(k in f.lower() for k in keywords):
                results.append(os.path.join(aten_dir, f))
        return results

    def _read(self, path):
        with open(path, "r", errors="ignore") as fh:
            return fh.read()
