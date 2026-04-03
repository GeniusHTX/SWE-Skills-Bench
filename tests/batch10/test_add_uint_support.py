"""
Test for 'add-uint-support' skill — PyTorch kUInt16/32/64 ReduceOps
Validates that the Agent added unsigned integer type support (kUInt16, kUInt32,
kUInt64) to PyTorch ReduceOps and CUDA kernels.
"""

import os
import re

import pytest


class TestAddUintSupport:
    """Verify PyTorch unsigned integer type additions."""

    REPO_DIR = "/workspace/pytorch"

    def test_uint_dtype_definitions_exist(self):
        """kUInt16, kUInt32, kUInt64 dtype definitions must exist."""
        found_types = set()
        for root, dirs, files in os.walk(os.path.join(self.REPO_DIR, "c10")):
            for f in files:
                if f.endswith((".h", ".cpp")):
                    path = os.path.join(root, f)
                    with open(path, "r", errors="ignore") as fh:
                        content = fh.read()
                    for dtype in ["kUInt16", "kUInt32", "kUInt64"]:
                        if dtype in content:
                            found_types.add(dtype)
        assert len(found_types) >= 2, (
            f"Only found {found_types}, expected kUInt16/kUInt32/kUInt64"
        )

    def test_reduce_ops_supports_uint(self):
        """ReduceOps must dispatch for unsigned integer types."""
        found = False
        for root, dirs, files in os.walk(os.path.join(self.REPO_DIR, "aten", "src", "ATen")):
            for f in files:
                if f.endswith((".cpp", ".h", ".cu")):
                    path = os.path.join(root, f)
                    with open(path, "r", errors="ignore") as fh:
                        content = fh.read()
                    if re.search(r"[Rr]educe", content) and re.search(r"kUInt16|kUInt32|kUInt64|uint16|uint32|uint64", content):
                        found = True
                        break
            if found:
                break
        assert found, "ReduceOps does not handle unsigned integer types"

    def test_cuda_kernel_supports_uint(self):
        """CUDA kernels must handle unsigned integer types."""
        found = False
        for root, dirs, files in os.walk(os.path.join(self.REPO_DIR, "aten", "src", "ATen")):
            for f in files:
                if f.endswith(".cu"):
                    path = os.path.join(root, f)
                    with open(path, "r", errors="ignore") as fh:
                        content = fh.read()
                    if re.search(r"uint16|uint32|uint64|kUInt", content):
                        found = True
                        break
            if found:
                break
        assert found, "No CUDA kernel handles unsigned integer types"

    def test_dtype_dispatch_macro_includes_uint(self):
        """AT_DISPATCH macro must include unsigned integer scalar types."""
        found = False
        for root, dirs, files in os.walk(os.path.join(self.REPO_DIR, "aten")):
            for f in files:
                if f.endswith((".cpp", ".h", ".cu")):
                    path = os.path.join(root, f)
                    with open(path, "r", errors="ignore") as fh:
                        content = fh.read()
                    if re.search(r"AT_DISPATCH.*uint", content, re.IGNORECASE):
                        found = True
                        break
            if found:
                break
        assert found, "AT_DISPATCH macro does not include uint types"

    def test_uint_types_registered_in_scalar_type(self):
        """ScalarType enum must include UInt16, UInt32, UInt64."""
        scalar_type_file = os.path.join(self.REPO_DIR, "c10", "core", "ScalarType.h")
        if not os.path.isfile(scalar_type_file):
            found = False
            for root, dirs, files in os.walk(os.path.join(self.REPO_DIR, "c10")):
                for f in files:
                    if "scalar" in f.lower() and f.endswith(".h"):
                        path = os.path.join(root, f)
                        with open(path, "r", errors="ignore") as fh:
                            content = fh.read()
                        if re.search(r"UInt16|UInt32|UInt64", content):
                            found = True
                            break
                if found:
                    break
            assert found, "UInt types not registered in ScalarType"
        else:
            with open(scalar_type_file, "r", errors="ignore") as fh:
                content = fh.read()
            assert re.search(r"UInt16|UInt32|UInt64", content), (
                "ScalarType.h does not define UInt16/UInt32/UInt64"
            )

    def test_python_bindings_for_uint(self):
        """Python bindings must expose torch.uint16, torch.uint32, or torch.uint64."""
        found = False
        for root, dirs, files in os.walk(os.path.join(self.REPO_DIR, "torch")):
            for f in files:
                if f.endswith(".py"):
                    path = os.path.join(root, f)
                    with open(path, "r", errors="ignore") as fh:
                        content = fh.read()
                    if re.search(r"uint16|uint32|uint64", content):
                        found = True
                        break
            if found:
                break
        assert found, "No Python bindings for uint types found"

    def test_reduce_test_for_uint(self):
        """Test files must include tests for reduce operations on unsigned int types."""
        found = False
        test_dirs = [
            os.path.join(self.REPO_DIR, "test"),
            os.path.join(self.REPO_DIR, "aten", "src", "ATen", "test"),
        ]
        for test_dir in test_dirs:
            if not os.path.isdir(test_dir):
                continue
            for root, dirs, files in os.walk(test_dir):
                for f in files:
                    if f.endswith((".py", ".cpp")):
                        path = os.path.join(root, f)
                        with open(path, "r", errors="ignore") as fh:
                            content = fh.read()
                        if re.search(r"reduce|sum|prod|mean", content, re.IGNORECASE) and re.search(r"uint16|uint32|uint64|kUInt", content):
                            found = True
                            break
                if found:
                    break
            if found:
                break
        assert found, "No reduce tests for unsigned integer types"

    def test_cpu_kernel_supports_uint(self):
        """CPU kernels must also handle unsigned integer types."""
        found = False
        for root, dirs, files in os.walk(os.path.join(self.REPO_DIR, "aten", "src", "ATen", "native")):
            for f in files:
                if f.endswith(".cpp"):
                    path = os.path.join(root, f)
                    with open(path, "r", errors="ignore") as fh:
                        content = fh.read()
                    if re.search(r"[Rr]educe", content) and re.search(r"uint16|uint32|uint64|kUInt", content):
                        found = True
                        break
            if found:
                break
        assert found, "CPU kernel does not handle unsigned integer types"

    def test_no_narrowing_conversion_warnings(self):
        """Code should not have obvious narrowing conversions from uint64 to int."""
        suspicious = False
        for root, dirs, files in os.walk(os.path.join(self.REPO_DIR, "aten", "src", "ATen")):
            for f in files:
                if f.endswith((".cpp", ".cu")):
                    path = os.path.join(root, f)
                    with open(path, "r", errors="ignore") as fh:
                        content = fh.read()
                    if re.search(r"static_cast<int>\s*\(\s*uint64", content):
                        suspicious = True
                        break
            if suspicious:
                break
        assert not suspicious, "Found suspicious narrowing cast from uint64 to int"

    def test_type_promotion_rules_for_uint(self):
        """Type promotion rules must handle unsigned integer types."""
        found = False
        for root, dirs, files in os.walk(os.path.join(self.REPO_DIR, "aten")):
            for f in files:
                if f.endswith((".cpp", ".h")):
                    path = os.path.join(root, f)
                    with open(path, "r", errors="ignore") as fh:
                        content = fh.read()
                    if re.search(r"promot", content, re.IGNORECASE) and re.search(r"uint|UInt", content):
                        found = True
                        break
            if found:
                break
        assert found, "Type promotion rules do not cover unsigned integer types"

    def test_uint_dtype_string_representation(self):
        """String representation for uint types must be defined."""
        found = False
        for root, dirs, files in os.walk(os.path.join(self.REPO_DIR, "c10")):
            for f in files:
                if f.endswith((".cpp", ".h")):
                    path = os.path.join(root, f)
                    with open(path, "r", errors="ignore") as fh:
                        content = fh.read()
                    if re.search(r'"uint16"|"uint32"|"uint64"', content):
                        found = True
                        break
            if found:
                break
        assert found, "String representations for uint types not found"
