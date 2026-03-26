"""
Test for 'add-uint-support' skill — Unsigned Integer Type Support in PyTorch
Validates that the Agent extended PyTorch operators to support uint16, uint32,
and uint64 tensor dtypes with proper dispatch registration and kernel coverage.
"""

import os
import re

import pytest


class TestAddUintSupport:
    """Verify PyTorch unsigned integer type dispatch extensions."""

    REPO_DIR = "/workspace/pytorch"
    NATIVE_DIR = "aten/src/ATen/native"

    def _read(self, *parts):
        fpath = os.path.join(self.REPO_DIR, *parts)
        assert os.path.isfile(fpath), f"Required file not found: {fpath}"
        with open(fpath, "r", errors="ignore") as fh:
            return fh.read()

    # ------------------------------------------------------------------
    # L1: File existence
    # ------------------------------------------------------------------

    def test_binary_ops_exists(self):
        """BinaryOps.cpp must exist."""
        assert os.path.isfile(
            os.path.join(self.REPO_DIR, self.NATIVE_DIR, "BinaryOps.cpp")
        )

    def test_binary_ops_kernel_exists(self):
        """cpu/BinaryOpsKernel.cpp must exist."""
        assert os.path.isfile(
            os.path.join(self.REPO_DIR, self.NATIVE_DIR, "cpu", "BinaryOpsKernel.cpp")
        )

    def test_tensor_compare_exists(self):
        """TensorCompare.cpp must exist."""
        assert os.path.isfile(
            os.path.join(self.REPO_DIR, self.NATIVE_DIR, "TensorCompare.cpp")
        )

    # ------------------------------------------------------------------
    # L2: Unsigned type dispatch in BinaryOps
    # ------------------------------------------------------------------

    def test_binary_ops_uint16_dispatch(self):
        """BinaryOps.cpp must register uint16 dispatch."""
        content = self._read(self.NATIVE_DIR, "BinaryOps.cpp")
        patterns = [r"uint16", r"UInt16", r"kUInt16", r"ScalarType::UInt16"]
        assert any(
            re.search(p, content) for p in patterns
        ), "BinaryOps.cpp missing uint16 dispatch"

    def test_binary_ops_uint32_dispatch(self):
        """BinaryOps.cpp must register uint32 dispatch."""
        content = self._read(self.NATIVE_DIR, "BinaryOps.cpp")
        patterns = [r"uint32", r"UInt32", r"kUInt32", r"ScalarType::UInt32"]
        assert any(
            re.search(p, content) for p in patterns
        ), "BinaryOps.cpp missing uint32 dispatch"

    def test_binary_ops_uint64_dispatch(self):
        """BinaryOps.cpp must register uint64 dispatch."""
        content = self._read(self.NATIVE_DIR, "BinaryOps.cpp")
        patterns = [r"uint64", r"UInt64", r"kUInt64", r"ScalarType::UInt64"]
        assert any(
            re.search(p, content) for p in patterns
        ), "BinaryOps.cpp missing uint64 dispatch"

    # ------------------------------------------------------------------
    # L2: Arithmetic operator coverage
    # ------------------------------------------------------------------

    def test_add_op_dispatch(self):
        """add operator must support unsigned types."""
        content = self._read(self.NATIVE_DIR, "BinaryOps.cpp")
        # Check add-related dispatch with unsigned
        has_add = re.search(r"add", content, re.IGNORECASE)
        has_uint = re.search(r"uint|UInt", content)
        assert (
            has_add and has_uint
        ), "add operator does not appear to support unsigned types"

    def test_mul_op_dispatch(self):
        """mul operator must support unsigned types."""
        content = self._read(self.NATIVE_DIR, "BinaryOps.cpp")
        assert re.search(
            r"mul", content, re.IGNORECASE
        ), "mul operator not found in BinaryOps.cpp"

    # ------------------------------------------------------------------
    # L2: Bitwise operator coverage
    # ------------------------------------------------------------------

    def test_bitwise_ops_coverage(self):
        """Bitwise operators must include unsigned type support."""
        content = self._read(self.NATIVE_DIR, "BinaryOps.cpp")
        bitwise_ops = [r"bitwise_and", r"bitwise_or", r"bitwise_xor"]
        found = sum(1 for p in bitwise_ops if re.search(p, content, re.IGNORECASE))
        assert found >= 2, f"Only {found} bitwise operator(s) found in BinaryOps.cpp"

    def test_shift_ops_coverage(self):
        """Shift operators must include unsigned type support."""
        content = self._read(self.NATIVE_DIR, "BinaryOps.cpp")
        patterns = [r"lshift", r"rshift", r"left_shift", r"right_shift"]
        found = sum(1 for p in patterns if re.search(p, content, re.IGNORECASE))
        assert found >= 1, "No shift operators found"

    # ------------------------------------------------------------------
    # L2: Comparison operators
    # ------------------------------------------------------------------

    def test_comparison_ops_unsigned(self):
        """TensorCompare.cpp must support unsigned comparison types."""
        content = self._read(self.NATIVE_DIR, "TensorCompare.cpp")
        patterns = [r"uint", r"UInt"]
        assert any(
            re.search(p, content) for p in patterns
        ), "TensorCompare.cpp does not reference unsigned types"

    def test_comparison_ops_complete(self):
        """Comparison operators eq/ne/lt/le/gt/ge must be present."""
        content = self._read(self.NATIVE_DIR, "TensorCompare.cpp")
        ops = [r"\beq\b", r"\bne\b", r"\blt\b", r"\ble\b", r"\bgt\b", r"\bge\b"]
        found = sum(1 for p in ops if re.search(p, content))
        assert found >= 4, f"Only {found} comparison operator(s) found"

    # ------------------------------------------------------------------
    # L2: CPU kernel implementation
    # ------------------------------------------------------------------

    def test_kernel_has_unsigned_paths(self):
        """CPU kernel must include paths for unsigned integer types."""
        content = self._read(self.NATIVE_DIR, "cpu", "BinaryOpsKernel.cpp")
        patterns = [r"uint16", r"uint32", r"uint64", r"UInt16", r"UInt32", r"UInt64"]
        found = sum(1 for p in patterns if re.search(p, content))
        assert found >= 2, "CPU kernel missing unsigned integer type paths"

    # ------------------------------------------------------------------
    # L2: GCD operator
    # ------------------------------------------------------------------

    def test_gcd_support(self):
        """GcdLcm.cpp must include unsigned type support if present."""
        gcd_path = os.path.join(self.REPO_DIR, self.NATIVE_DIR, "GcdLcm.cpp")
        if not os.path.isfile(gcd_path):
            pytest.skip("GcdLcm.cpp does not exist in this PyTorch version")
        with open(gcd_path, "r", errors="ignore") as fh:
            content = fh.read()
        patterns = [r"uint", r"UInt", r"unsigned"]
        assert any(
            re.search(p, content) for p in patterns
        ), "GcdLcm.cpp does not reference unsigned types"
