"""
Test for 'add-uint-support' skill — PyTorch Unsigned Integer Dispatch
Validates that the Agent added uint16/32/64 support to min, max, clamp,
bitwise, and where operations in the PyTorch ATen dispatch layer.
"""

import os
import re
import sys

import pytest


class TestAddUintSupport:
    """Verify PyTorch unsigned integer dispatch support."""

    REPO_DIR = "/workspace/pytorch"

    @staticmethod
    def _read(path: str) -> str:
        try:
            with open(path, "r", errors="ignore") as fh:
                return fh.read()
        except OSError:
            return ""

    # ── file_path_check ─────────────────────────────────────────────

    def test_reduce_ops_cpp_exists(self):
        """Verify ReduceOps.cpp and TensorCompare.cpp source files exist."""
        for rel in (
            "aten/src/ATen/native/ReduceOps.cpp",
            "aten/src/ATen/native/TensorCompare.cpp",
        ):
            path = os.path.join(self.REPO_DIR, rel)
            assert os.path.isfile(path), f"Missing: {rel}"

    def test_binary_ops_kernel_exists(self):
        """Verify BinaryOpsKernel.cpp and CUDA counterpart files exist."""
        for rel in (
            "aten/src/ATen/native/cpu/BinaryOpsKernel.cpp",
            "aten/src/ATen/native/cuda/BinaryBitwiseOpsKernels.cu",
        ):
            path = os.path.join(self.REPO_DIR, rel)
            assert os.path.isfile(path), f"Missing: {rel}"

    def test_cuda_reduce_kernel_exists(self):
        """Verify CUDA ReduceMinMaxKernel.cu exists for GPU path support."""
        path = os.path.join(self.REPO_DIR, "aten/src/ATen/native/cuda/ReduceMinMaxKernel.cu")
        assert os.path.isfile(path), "ReduceMinMaxKernel.cu missing"

    # ── semantic_check ──────────────────────────────────────────────

    def test_at_dispatch_v2_used_in_reduce_ops(self):
        """Verify AT_DISPATCH_V2 macro is used instead of legacy AT_DISPATCH_ALL_TYPES in min/max kernels."""
        content = self._read(os.path.join(self.REPO_DIR, "aten/src/ATen/native/ReduceOps.cpp"))
        assert content, "ReduceOps.cpp is empty or unreadable"
        assert "AT_DISPATCH_V2" in content, \
            "AT_DISPATCH_V2 macro not found in ReduceOps.cpp"

    def test_unsigned_type_group_in_dispatch(self):
        """Verify unsigned type group macro or individual uint types are referenced."""
        content = self._read(os.path.join(self.REPO_DIR, "aten/src/ATen/native/ReduceOps.cpp"))
        assert content, "ReduceOps.cpp is empty or unreadable"
        found = any(kw in content for kw in (
            "AT_BAREBONES_UNSIGNED_TYPES", "AT_INTEGRAL_TYPES_V2",
            "kUInt16", "kUInt32", "kUInt64",
        ))
        assert found, "No unsigned type group or individual uint type found in ReduceOps.cpp"

    def test_binary_ops_unsigned_dispatch(self):
        """Verify BinaryOpsKernel.cpp includes unsigned type group in bitwise ops dispatch."""
        content = self._read(os.path.join(
            self.REPO_DIR, "aten/src/ATen/native/cpu/BinaryOpsKernel.cpp"))
        assert content, "BinaryOpsKernel.cpp is empty or unreadable"
        found = any(kw in content for kw in (
            "AT_DISPATCH_V2", "AT_BAREBONES_UNSIGNED_TYPES", "kUInt16",
        ))
        assert found, "Unsigned type support not visible in binary ops kernel dispatch"

    # ── functional_check (import) ───────────────────────────────────

    def _skip_unless_torch(self):
        try:
            import torch  # noqa: F401
        except ImportError:
            pytest.skip("torch not importable — build may not be available")

    def test_torch_min_uint32(self):
        """torch.min on a uint32 tensor returns correct minimum scalar value."""
        self._skip_unless_torch()
        import torch
        t = torch.tensor([3, 1, 2], dtype=torch.uint32)
        result = torch.min(t).item()
        assert result == 1, f"Expected 1, got {result}"

    def test_torch_max_uint32_boundary(self):
        """torch.max on uint32 tensor with value 2**32-1 returns 4294967295 without overflow."""
        self._skip_unless_torch()
        import torch
        t = torch.tensor([0, 4294967295], dtype=torch.uint32)
        result = torch.max(t).item()
        assert result == 4294967295, f"Expected 4294967295, got {result}"

    def test_torch_clamp_uint16(self):
        """torch.clamp on uint16 tensor with min/max scalars produces correctly clamped output."""
        self._skip_unless_torch()
        import torch
        t = torch.tensor([0, 500, 1000], dtype=torch.uint16)
        r = torch.clamp(t, min=100, max=800)
        assert r.tolist() == [100, 500, 800], f"Unexpected clamp result: {r.tolist()}"

    def test_torch_bitwise_and_uint16(self):
        """torch.bitwise_and on uint16 tensors returns bit-exact unsigned result."""
        self._skip_unless_torch()
        import torch
        a = torch.tensor([0xFF00], dtype=torch.uint16)
        b = torch.tensor([0x0F0F], dtype=torch.uint16)
        result = torch.bitwise_and(a, b).item()
        assert result == 3840, f"Expected 3840 (0x0F00), got {result}"

    def test_torch_where_uint64(self):
        """torch.where with boolean mask on uint64 tensors preserves dtype and values."""
        self._skip_unless_torch()
        import torch
        cond = torch.tensor([True, False, True])
        x = torch.tensor([10, 20, 30], dtype=torch.uint64)
        y = torch.tensor([40, 50, 60], dtype=torch.uint64)
        result = torch.where(cond, x, y).tolist()
        assert result == [10, 50, 30], f"Unexpected where result: {result}"
