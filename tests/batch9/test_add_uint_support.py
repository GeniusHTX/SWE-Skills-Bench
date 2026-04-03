"""
Test for 'add-uint-support' skill — CUDA uint32/uint64 Support
Validates CUDA kernel source, dtype header enum, build system,
template instantiation, division guard, and bounds checking.
"""

import glob
import os
import re

import pytest


class TestAddUintSupport:
    """Verify CUDA uint support: kernel, dtypes, build, safety guards."""

    REPO_DIR = "/workspace/pytorch"

    # ── helpers ──────────────────────────────────────────────────────────

    @staticmethod
    def _read_file(path: str) -> str:
        try:
            with open(path, "r", errors="ignore") as fh:
                return fh.read()
        except OSError:
            return ""

    def _root(self, *parts) -> str:
        return os.path.join(self.REPO_DIR, *parts)

    def _uint_ops_path(self) -> str:
        for candidate in ("src/kernels/uint_ops.cu", "src/cuda/uint_ops.cu"):
            p = self._root(candidate)
            if os.path.isfile(p):
                return p
        return ""

    def _dtypes_header_path(self) -> str:
        for candidate in ("include/dtypes.h", "include/tensor.h"):
            p = self._root(candidate)
            if os.path.isfile(p):
                return p
        return ""

    # ── file_path_check ──────────────────────────────────────────────────

    def test_uint_ops_cu_exists(self):
        """CUDA uint_ops.cu kernel must exist."""
        path = self._uint_ops_path()
        assert path, "uint_ops.cu not found in src/kernels/ or src/cuda/"
        assert os.path.getsize(path) > 0

    def test_dtypes_header_has_uint_enums(self):
        """dtypes header must contain UINT32 and UINT64."""
        path = self._dtypes_header_path()
        assert path, "dtypes.h or tensor.h not found in include/"
        content = self._read_file(path)
        assert "UINT32" in content, "UINT32 not in dtypes header"
        assert "UINT64" in content, "UINT64 not in dtypes header"

    def test_build_system_references_uint_ops(self):
        """CMakeLists.txt or setup.py must reference uint_ops.cu."""
        cmake = self._read_file(self._root("CMakeLists.txt"))
        setup = self._read_file(self._root("setup.py"))
        assert "uint_ops.cu" in cmake or "uint_ops.cu" in setup, \
            "uint_ops.cu not in CMakeLists.txt or setup.py"

    # ── semantic_check ───────────────────────────────────────────────────

    def test_template_instantiated_for_uint32_and_uint64(self):
        """Kernel must use uint32_t and uint64_t template types."""
        path = self._uint_ops_path()
        if not path:
            pytest.skip("uint_ops.cu not found")
        content = self._read_file(path)
        assert "uint32_t" in content, "No uint32_t in kernel"
        assert "uint64_t" in content, "No uint64_t in kernel"

    def test_division_by_zero_guard(self):
        """Division kernel must guard against zero divisor."""
        path = self._uint_ops_path()
        if not path:
            pytest.skip("uint_ops.cu not found")
        content = self._read_file(path)
        # Check for any form of zero-divisor guard
        has_guard = re.search(r"(==\s*0|!=\s*0|== 0)", content) is not None
        assert has_guard, "No division-by-zero guard in uint_ops.cu"

    def test_thread_index_bounds_check(self):
        """Kernel must check thread index against array size."""
        path = self._uint_ops_path()
        if not path:
            pytest.skip("uint_ops.cu not found")
        content = self._read_file(path)
        assert "threadIdx" in content or "blockIdx" in content
        has_bound = re.search(r"if\s*\(.*<\s*(n|size|num)", content) is not None
        assert has_bound, "No bounds check on thread index"

    def test_dtype_enum_contains_both_uints(self):
        """Dtype enum must include both UINT32 and UINT64 entries."""
        path = self._dtypes_header_path()
        if not path:
            pytest.skip("dtypes header not found")
        content = self._read_file(path)
        assert "enum" in content.lower()
        assert "UINT32" in content
        assert "UINT64" in content

    # ── functional_check ─────────────────────────────────────────────────

    def test_overflow_wrapping_documented(self):
        """Test or kernel must reference uint32 overflow behavior."""
        test_path = self._root("tests", "test_uint_ops.py")
        kernel_path = self._uint_ops_path()
        test_content = self._read_file(test_path)
        kernel_content = self._read_file(kernel_path) if kernel_path else ""
        combined = test_content + kernel_content
        has_overflow = any(
            s in combined
            for s in ("UINT32_MAX", "0xFFFFFFFF", "4294967295", "overflow", "wrapping")
        )
        assert has_overflow, "No overflow/wrapping reference in test or kernel"

    def test_single_element_edge_case(self):
        """Test file must cover single-element array edge case."""
        content = self._read_file(self._root("tests", "test_uint_ops.py"))
        if not content:
            pytest.skip("test_uint_ops.py not found")
        has_single = any(s in content for s in ("size=1", "n=1", "len=1", "single"))
        assert has_single, "No single-element test case"

    def test_zero_length_edge_case(self):
        """Test file must cover zero-length array edge case."""
        content = self._read_file(self._root("tests", "test_uint_ops.py"))
        if not content:
            pytest.skip("test_uint_ops.py not found")
        has_zero = any(s in content for s in ("size=0", "n=0", "empty", "zero"))
        assert has_zero, "No zero-length test case"

    def test_no_signed_type_for_uint_ops(self):
        """Kernel must not use int32_t where uint32_t is required."""
        path = self._uint_ops_path()
        if not path:
            pytest.skip("uint_ops.cu not found")
        content = self._read_file(path)
        # Must have unsigned types
        assert "uint32_t" in content
        # Verify no signed int32_t in dispatch logic for uint operations
        lines = content.split("\n")
        for i, line in enumerate(lines):
            if "int32_t" in line and "uint32_t" not in line:
                # Allow in comments
                stripped = line.strip()
                if stripped.startswith("//") or stripped.startswith("/*"):
                    continue
                # Allow in non-uint dispatch paths
                if "UINT" not in line and "uint" not in line:
                    continue
                pytest.fail(f"Signed int32_t used in uint context at line {i+1}: {line.strip()}")
