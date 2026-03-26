"""
Tests for the add-uint-support skill.
Verifies that PyTorch uint32/uint64 operator support is correctly introduced,
including the new AT_DISPATCH_ALL_TYPES_AND_UINT macro in Dispatch.h,
test file presence, and mocked functional behavior of uint tensor operations.
"""

import os
import sys
import unittest.mock as mock

import pytest

REPO_DIR = "/workspace/pytorch"


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _path(rel: str) -> str:
    return os.path.join(REPO_DIR, rel)


def _read(rel: str) -> str:
    full = _path(rel)
    if not os.path.isfile(full):
        pytest.skip(f"File not found: {full}")
    with open(full, encoding="utf-8", errors="replace") as fh:
        return fh.read()


def _try_import_torch():
    """Skip test if torch is not importable."""
    try:
        import torch  # noqa: F401

        return torch
    except ImportError:
        pytest.skip("torch not available; functional checks skipped")


# ---------------------------------------------------------------------------
# File path checks
# ---------------------------------------------------------------------------


class TestAddUintSupport:
    """Test suite for PyTorch uint32/uint64 dispatch support skill."""

    def test_dispatch_header_file_exists(self):
        """Verify Dispatch.h is present in the expected ATen location."""
        target = _path("aten/src/ATen/Dispatch.h")
        assert os.path.isfile(target), f"Dispatch.h not found: {target}"

    def test_unary_and_binary_ops_files_exist(self):
        """Verify UnaryOps.cpp and BinaryOps.cpp files exist."""
        for rel in (
            "aten/src/ATen/native/UnaryOps.cpp",
            "aten/src/ATen/native/BinaryOps.cpp",
        ):
            assert os.path.isfile(_path(rel)), f"Missing required file: {rel}"

    def test_test_file_exists(self):
        """Verify Python test file for uint support exists."""
        target = _path("test/test_uint_support.py")
        assert os.path.isfile(target), f"Test file not found: {target}"

    # -----------------------------------------------------------------------
    # Semantic checks
    # -----------------------------------------------------------------------

    def test_dispatch_h_defines_uint_dispatch_macro(self):
        """Verify Dispatch.h defines AT_DISPATCH_ALL_TYPES_AND_UINT macro."""
        content = _read("aten/src/ATen/Dispatch.h")
        assert (
            "AT_DISPATCH_ALL_TYPES_AND_UINT" in content
        ), "Dispatch.h must define the AT_DISPATCH_ALL_TYPES_AND_UINT macro"

    def test_dispatch_h_includes_kuint32_kuint64(self):
        """Verify Dispatch.h includes kUInt32 and kUInt64 tokens in the new dispatch macro."""
        content = _read("aten/src/ATen/Dispatch.h")
        assert "kUInt32" in content, "Dispatch.h must contain kUInt32"
        assert "kUInt64" in content, "Dispatch.h must contain kUInt64"

    def test_original_dispatch_macro_unchanged(self):
        """Verify original AT_DISPATCH_ALL_TYPES macro still exists and is not removed."""
        content = _read("aten/src/ATen/Dispatch.h")
        assert (
            "AT_DISPATCH_ALL_TYPES" in content
        ), "Original AT_DISPATCH_ALL_TYPES macro must remain in Dispatch.h"

    def test_unary_ops_uses_uint_dispatch(self):
        """Verify UnaryOps.cpp references the new AT_DISPATCH_ALL_TYPES_AND_UINT macro."""
        content = _read("aten/src/ATen/native/UnaryOps.cpp")
        assert (
            "AT_DISPATCH_ALL_TYPES_AND_UINT" in content
        ), "UnaryOps.cpp must use AT_DISPATCH_ALL_TYPES_AND_UINT macro"

    # -----------------------------------------------------------------------
    # Functional checks (mocked - PyTorch build is required for real execution)
    # -----------------------------------------------------------------------

    def test_neg_operation_on_uint32_raises_runtime_error(self):
        """Verify that negation on uint32 tensor raises RuntimeError (unsigned cannot be negated)."""
        torch = _try_import_torch()
        if not hasattr(torch, "uint32"):
            pytest.skip("torch.uint32 not available in this PyTorch build")
        x = torch.tensor([1, 2, 3], dtype=torch.uint32)
        with pytest.raises(RuntimeError):
            _ = -x

    def test_uint64_tensor_creation(self):
        """Verify that torch.uint64 dtype can be used to create a tensor without error."""
        torch = _try_import_torch()
        if not hasattr(torch, "uint64"):
            pytest.skip("torch.uint64 not available in this PyTorch build")
        x = torch.tensor([1, 2, 3], dtype=torch.uint64)
        assert x.dtype == torch.uint64, f"Expected dtype uint64, got {x.dtype}"

    def test_uint32_max_value_roundtrip(self):
        """Verify uint32 max value (4294967295) can be stored and retrieved accurately."""
        torch = _try_import_torch()
        if not hasattr(torch, "uint32"):
            pytest.skip("torch.uint32 not available in this PyTorch build")
        x = torch.tensor([4294967295], dtype=torch.uint32)
        val = x[0].item()
        assert val == 4294967295, f"Expected 4294967295, got {val}"

    def test_div_by_zero_uint32_raises_runtime_error(self):
        """Verify that dividing a uint32 tensor by zero raises RuntimeError."""
        torch = _try_import_torch()
        if not hasattr(torch, "uint32"):
            pytest.skip("torch.uint32 not available in this PyTorch build")
        a = torch.tensor([4], dtype=torch.uint32)
        b = torch.tensor([0], dtype=torch.uint32)
        with pytest.raises(RuntimeError):
            _ = a / b

    def test_sub_underflow_wraps_for_uint32(self):
        """Verify uint32 subtraction wraps around on underflow (0 - 1 = 2^32-1)."""
        torch = _try_import_torch()
        if not hasattr(torch, "uint32"):
            pytest.skip("torch.uint32 not available in this PyTorch build")
        a = torch.tensor([0], dtype=torch.uint32)
        b = torch.tensor([1], dtype=torch.uint32)
        result = a - b
        assert (
            result[0].item() == 4294967295
        ), f"uint32(0) - uint32(1) should wrap to 4294967295, got {result[0].item()}"
