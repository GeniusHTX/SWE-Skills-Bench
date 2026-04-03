"""
Test for 'add-uint-support' skill — Restore uint32/uint64 operator support in PyTorch
Validates that the Agent updated CUDA and CPU kernel files to use AT_DISPATCH_V2
and added unsigned integer type support for reduce operations.
"""

import os
import re

import pytest


class TestAddUintSupport:
    """Verify PyTorch unsigned-int operator restore."""

    REPO_DIR = "/workspace/pytorch"

    @staticmethod
    def _read(path):
        with open(path, "r", errors="ignore") as fh:
            return fh.read()

    # ---- file_path_check ----

    def test_reduce_min_max_kernel_cu_exists(self):
        """Verifies aten/src/ATen/native/cuda/ReduceMinMaxKernel.cu exists."""
        path = os.path.join(
            self.REPO_DIR, "aten/src/ATen/native/cuda/ReduceMinMaxKernel.cu"
        )
        assert os.path.exists(path), f"Expected file not found: {path}"

    def test_reduce_ops_kernel_cu_exists(self):
        """Verifies aten/src/ATen/native/cuda/ReduceOpsKernel.cu exists."""
        path = os.path.join(
            self.REPO_DIR, "aten/src/ATen/native/cuda/ReduceOpsKernel.cu"
        )
        assert os.path.exists(path), f"Expected file not found: {path}"

    def test_reduce_ops_kernel_cpp_exists(self):
        """Verifies aten/src/ATen/native/cpu/ReduceOpsKernel.cpp exists."""
        path = os.path.join(
            self.REPO_DIR, "aten/src/ATen/native/cpu/ReduceOpsKernel.cpp"
        )
        assert os.path.exists(path), f"Expected file not found: {path}"

    def test_reduce_ops_cpp_exists(self):
        """Verifies aten/src/ATen/native/ReduceOps.cpp exists."""
        path = os.path.join(self.REPO_DIR, "aten/src/ATen/native/ReduceOps.cpp")
        assert os.path.exists(path), f"Expected file not found: {path}"

    # ---- semantic_check ----

    def test_cuda_min_uses_at_dispatch_v2(self):
        """ReduceMinMaxKernel.cu must use AT_DISPATCH_V2 macro."""
        path = os.path.join(
            self.REPO_DIR, "aten/src/ATen/native/cuda/ReduceMinMaxKernel.cu"
        )
        cuda_min_text = self._read(path)
        assert (
            "AT_DISPATCH_V2" in cuda_min_text
        ), "AT_DISPATCH_V2 not used in ReduceMinMaxKernel.cu"

    def test_cuda_min_has_unsigned_int_types(self):
        """ReduceMinMaxKernel.cu must reference unsigned int types."""
        path = os.path.join(
            self.REPO_DIR, "aten/src/ATen/native/cuda/ReduceMinMaxKernel.cu"
        )
        cuda_min_text = self._read(path)
        uint_keywords = [
            "kUInt16",
            "kUInt32",
            "kUInt64",
            "AT_UNSIGNED_INT_TYPES",
            "at::kUInt",
        ]
        assert any(
            k in cuda_min_text for k in uint_keywords
        ), "Unsigned int types not found in ReduceMinMaxKernel.cu"

    def test_cuda_ops_uses_at_dispatch_v2(self):
        """ReduceOpsKernel.cu must use AT_DISPATCH_V2 macro."""
        path = os.path.join(
            self.REPO_DIR, "aten/src/ATen/native/cuda/ReduceOpsKernel.cu"
        )
        cuda_ops_text = self._read(path)
        assert (
            "AT_DISPATCH_V2" in cuda_ops_text
        ), "AT_DISPATCH_V2 not used in ReduceOpsKernel.cu"

    def test_cuda_ops_has_unsigned_int_types(self):
        """ReduceOpsKernel.cu must reference unsigned int types."""
        path = os.path.join(
            self.REPO_DIR, "aten/src/ATen/native/cuda/ReduceOpsKernel.cu"
        )
        cuda_ops_text = self._read(path)
        uint_keywords = ["kUInt16", "kUInt32", "kUInt64", "AT_UNSIGNED_INT_TYPES"]
        assert any(
            k in cuda_ops_text for k in uint_keywords
        ), "Unsigned int types not found in ReduceOpsKernel.cu"

    def test_cpu_reduce_ops_readable(self):
        """CPU ReduceOpsKernel.cpp can be read successfully."""
        path = os.path.join(
            self.REPO_DIR, "aten/src/ATen/native/cpu/ReduceOpsKernel.cpp"
        )
        content = self._read(path)
        assert len(content) > 0, "ReduceOpsKernel.cpp is empty"

    def test_reduce_ops_cpp_readable(self):
        """ReduceOps.cpp can be read successfully."""
        path = os.path.join(self.REPO_DIR, "aten/src/ATen/native/ReduceOps.cpp")
        content = self._read(path)
        assert len(content) > 0, "ReduceOps.cpp is empty"

    # ---- functional_check ----

    def test_mean_operator_excludes_unsigned_int(self):
        """mean operator should NOT have unsigned int support (mathematically invalid)."""
        path = os.path.join(self.REPO_DIR, "aten/src/ATen/native/ReduceOps.cpp")
        reduce_text = self._read(path)
        if "mean" in reduce_text:
            idx = reduce_text.find("mean")
            mean_section = reduce_text[idx : idx + 500]
        else:
            mean_section = ""
        assert not any(
            k in mean_section for k in ["kUInt16", "kUInt32", "kUInt64"]
        ), "mean operator should NOT have unsigned int support"

    def test_both_cuda_files_use_dispatch_v2(self):
        """Both CUDA files must use AT_DISPATCH_V2 consistently."""
        cuda_min = os.path.join(
            self.REPO_DIR, "aten/src/ATen/native/cuda/ReduceMinMaxKernel.cu"
        )
        cuda_ops = os.path.join(
            self.REPO_DIR, "aten/src/ATen/native/cuda/ReduceOpsKernel.cu"
        )
        cuda_min_text = self._read(cuda_min)
        cuda_ops_text = self._read(cuda_ops)
        assert (
            "AT_DISPATCH_V2" in cuda_min_text and "AT_DISPATCH_V2" in cuda_ops_text
        ), "Both CUDA files must use AT_DISPATCH_V2"

    def test_no_legacy_dispatch_macros_in_cuda_min(self):
        """Legacy AT_DISPATCH_ALL_TYPES_AND_COMPLEX macros must be removed from ReduceMinMaxKernel.cu."""
        path = os.path.join(
            self.REPO_DIR, "aten/src/ATen/native/cuda/ReduceMinMaxKernel.cu"
        )
        cuda_min_text = self._read(path)
        legacy_patterns = [
            "AT_DISPATCH_ALL_TYPES_AND_COMPLEX_AND3",
            "AT_DISPATCH_ALL_TYPES_AND_COMPLEX_AND4",
        ]
        for p in legacy_patterns:
            assert (
                p not in cuda_min_text
            ), f"Legacy macro {p} still in ReduceMinMaxKernel.cu"

    def test_cpu_and_cuda_consistency(self):
        """CPU counterpart must also be updated when CUDA files are changed."""
        cuda_min = os.path.join(
            self.REPO_DIR, "aten/src/ATen/native/cuda/ReduceMinMaxKernel.cu"
        )
        cpu_ops = os.path.join(
            self.REPO_DIR, "aten/src/ATen/native/cpu/ReduceOpsKernel.cpp"
        )
        cuda_min_text = self._read(cuda_min)
        cpu_text = self._read(cpu_ops)
        cuda_has_uint = any(
            k in cuda_min_text
            for k in ["kUInt16", "kUInt32", "kUInt64", "AT_UNSIGNED_INT_TYPES"]
        )
        cpu_has_dispatch_or_uint = "AT_DISPATCH_V2" in cpu_text or any(
            k in cpu_text
            for k in ["kUInt16", "kUInt32", "kUInt64", "AT_UNSIGNED_INT_TYPES"]
        )
        if cuda_has_uint:
            assert cpu_has_dispatch_or_uint, (
                "CUDA updated with uint support but CPU counterpart not updated — "
                "consistency check fails"
            )
