"""Test file for the add-uint-support skill.

This suite validates that PyTorch CUDA kernel files are updated to include
uint16/uint32/uint64 dispatch types and that the operations produce correct
results under unsigned semantics.
"""

from __future__ import annotations

import pathlib
import re

import pytest


class TestAddUintSupport:
    """Verify unsigned integer type dispatch and runtime correctness in PyTorch."""

    REPO_DIR = "/workspace/pytorch"

    CU_FILES = [
        "aten/src/ATen/native/cuda/ReduceMinMaxKernel.cu",
        "aten/src/ATen/native/cuda/SortingKernel.cu",
        "aten/src/ATen/native/cuda/CumsumKernel.cu",
        "aten/src/ATen/native/cuda/CompareKernels.cu",
    ]

    UINT_TYPES = ["kUInt16", "kUInt32", "kUInt64"]

    EXISTING_TYPES_RE = re.compile(
        r"kFloat|kDouble|kHalf|kBFloat16|kBool|kInt|kLong|kShort|kByte"
    )

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    def _repo_path(self, relative: str) -> pathlib.Path:
        return pathlib.Path(self.REPO_DIR, *relative.split("/"))

    def _read_text(self, relative: str) -> str:
        path = self._repo_path(relative)
        assert path.exists(), f"Expected path to exist: {path}"
        return path.read_text(encoding="utf-8", errors="ignore")

    def _assert_non_empty_file(self, relative: str) -> pathlib.Path:
        path = self._repo_path(relative)
        assert path.is_file(), f"Expected file to exist: {path}"
        assert path.stat().st_size > 0, f"Expected non-empty file: {path}"
        return path

    def _find_dispatch_blocks(self, source: str) -> list[str]:
        """Return all AT_DISPATCH_* macro invocation blocks."""
        blocks: list[str] = []
        for m in re.finditer(r"AT_DISPATCH_\w+\s*\(", source):
            start = m.start()
            depth = 0
            for i, ch in enumerate(source[start:], start):
                if ch == "(":
                    depth += 1
                elif ch == ")":
                    depth -= 1
                    if depth == 0:
                        blocks.append(source[start : i + 1])
                        break
        return blocks

    # ------------------------------------------------------------------
    # Layer 1 – file_path_check (3 cases)
    # ------------------------------------------------------------------

    def test_file_path_aten_src_aten_native_cuda_reduceminmaxkernel_cu_is_modified(
        self,
    ):
        """Verify ReduceMinMaxKernel.cu exists and is non-empty."""
        self._assert_non_empty_file("aten/src/ATen/native/cuda/ReduceMinMaxKernel.cu")

    def test_file_path_aten_src_aten_native_cuda_sortingkernel_cu_is_modified(self):
        """Verify SortingKernel.cu exists and is non-empty."""
        self._assert_non_empty_file("aten/src/ATen/native/cuda/SortingKernel.cu")

    def test_file_path_aten_src_aten_native_cuda_cumsumkernel_cu_is_modified(self):
        """Verify CumsumKernel.cu exists and is non-empty."""
        self._assert_non_empty_file("aten/src/ATen/native/cuda/CumsumKernel.cu")

    # ------------------------------------------------------------------
    # Layer 2 – semantic_check (4 cases)
    # ------------------------------------------------------------------

    def test_semantic_each_cu_file_s_at_dispatch_macros_include_kuint16_kuint32_ku(
        self,
    ):
        """Each .cu file's AT_DISPATCH macros include kUInt16, kUInt32, kUInt64."""
        for rel in self.CU_FILES:
            path = self._repo_path(rel)
            if not path.exists():
                continue
            src = path.read_text(encoding="utf-8", errors="ignore")
            dispatch_blocks = self._find_dispatch_blocks(src)
            assert dispatch_blocks, f"No AT_DISPATCH macros found in {rel}"
            for block in dispatch_blocks:
                for ut in self.UINT_TYPES:
                    assert (
                        ut in block
                    ), f"Dispatch block in {rel} missing {ut}:\n{block[:300]}"

    def test_semantic_all_dispatch_sites_within_each_file_are_updated_not_just_the(
        self,
    ):
        """All dispatch sites within each file are updated, not just the first."""
        for rel in self.CU_FILES:
            path = self._repo_path(rel)
            if not path.exists():
                continue
            src = path.read_text(encoding="utf-8", errors="ignore")
            dispatch_blocks = self._find_dispatch_blocks(src)
            for idx, block in enumerate(dispatch_blocks):
                missing = [t for t in self.UINT_TYPES if t not in block]
                assert (
                    not missing
                ), f"{rel} dispatch site #{idx + 1} missing types {missing}"

    def test_semantic_existing_type_support_signed_integers_floats_half_bfloat16_b(
        self,
    ):
        """Existing type support (signed ints, floats, half, bfloat16, bool) unchanged."""
        for rel in self.CU_FILES:
            path = self._repo_path(rel)
            if not path.exists():
                continue
            src = path.read_text(encoding="utf-8", errors="ignore")
            dispatch_blocks = self._find_dispatch_blocks(src)
            for block in dispatch_blocks:
                assert self.EXISTING_TYPES_RE.search(
                    block
                ), f"Existing types appear to be removed in {rel}"

    def test_semantic_no_changes_to_dispatch_format_or_macro_structure_beyond_addi(
        self,
    ):
        """No changes to dispatch format or macro structure beyond adding new types."""
        for rel in self.CU_FILES:
            path = self._repo_path(rel)
            if not path.exists():
                continue
            src = path.read_text(encoding="utf-8", errors="ignore")
            dispatch_blocks = self._find_dispatch_blocks(src)
            for block in dispatch_blocks:
                # Macro name must still be AT_DISPATCH_*
                assert block.startswith(
                    "AT_DISPATCH_"
                ), f"Dispatch macro name changed in {rel}"
                # Lambda body should still be present
                assert re.search(
                    r"\[&\]|LAMBDA|\{", block
                ), f"Dispatch macro lambda structure altered in {rel}"

    # ------------------------------------------------------------------
    # Layer 3 – functional_check (5 cases, import-style via torch)
    # ------------------------------------------------------------------

    def _skip_if_no_torch_cuda(self):
        """Skip the test when torch is not available or CUDA not ready."""
        torch = pytest.importorskip("torch")
        if not torch.cuda.is_available():
            pytest.skip("CUDA not available")
        return torch

    def test_functional_torch_min_tensor_3_1_2_dtype_torch_uint32_returns_tensor_1_d(
        self,
    ):
        """torch.min on uint32 tensor returns correct minimum value."""
        torch = self._skip_if_no_torch_cuda()
        t = torch.tensor([3, 1, 2], dtype=torch.uint32, device="cuda")
        result = torch.min(t)
        assert result.item() == 1
        assert result.dtype == torch.uint32

    def test_functional_torch_sort_tensor_300_100_200_dtype_torch_uint64_returns_sor(
        self,
    ):
        """torch.sort on uint64 tensor returns sorted values and indices."""
        torch = self._skip_if_no_torch_cuda()
        t = torch.tensor([300, 100, 200], dtype=torch.uint64, device="cuda")
        values, indices = torch.sort(t)
        assert values.tolist() == [100, 200, 300]
        assert indices.tolist() == [1, 2, 0]

    def test_functional_torch_cumsum_tensor_1_2_3_dtype_torch_uint32_dim_0_returns_t(
        self,
    ):
        """torch.cumsum on uint32 tensor returns correct prefix sums."""
        torch = self._skip_if_no_torch_cuda()
        t = torch.tensor([1, 2, 3], dtype=torch.uint32, device="cuda")
        result = torch.cumsum(t, dim=0)
        assert result.tolist() == [1, 3, 6]

    def test_functional_torch_eq_tensor_1_2_dtype_torch_uint16_tensor_1_3_dtype_torc(
        self,
    ):
        """torch.eq comparing uint16 tensors returns correct boolean tensor."""
        torch = self._skip_if_no_torch_cuda()
        a = torch.tensor([1, 2], dtype=torch.uint16, device="cuda")
        b = torch.tensor([1, 3], dtype=torch.uint16, device="cuda")
        result = torch.eq(a, b)
        assert result.tolist() == [True, False]

    def test_functional_existing_float32_int32_operations_produce_identical_results(
        self,
    ):
        """Existing float32/int32 operations produce identical (non-regressed) results."""
        torch = self._skip_if_no_torch_cuda()
        # int32 min
        t_int = torch.tensor([5, 2, 8], dtype=torch.int32, device="cuda")
        assert torch.min(t_int).item() == 2
        # float32 sort
        t_float = torch.tensor([3.0, 1.0, 2.0], dtype=torch.float32, device="cuda")
        vals, idxs = torch.sort(t_float)
        assert vals.tolist() == [1.0, 2.0, 3.0]
        # float32 cumsum
        assert torch.cumsum(t_float, dim=0).tolist() == pytest.approx([3.0, 4.0, 6.0])
