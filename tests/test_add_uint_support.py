"""
Unit Test for UInt32/64 Operator Support in PyTorch
"""

import torch
import pytest


class TestUIntOperators:
    """Tests for uint32 and uint64 operator support."""

    @pytest.fixture(params=["uint32", "uint64"])
    def dtype(self, request):
        """Parametrized fixture: uint32 and uint64."""
        dtype_map = {
            "uint32": torch.uint32,
            "uint64": torch.uint64,
        }
        return dtype_map[request.param]

    # =========================================================================
    # Supported group: these 3 operators typically support uint32/64 in PyTorch
    # =========================================================================

    def test_bitwise_and(self, dtype):
        """Test bitwise_and operation (already supported)."""
        a = torch.tensor(0b1100, dtype=dtype)  # 12
        b = torch.tensor(0b1010, dtype=dtype)  # 10
        result = torch.bitwise_and(a, b)
        expected = torch.tensor(0b1000, dtype=dtype)  # 8
        assert torch.equal(result, expected), f"bitwise_and failed for {dtype}"

    def test_mul(self, dtype):
        """Test multiplication operation (already supported)."""
        a = torch.tensor(3, dtype=dtype)
        b = torch.tensor(4, dtype=dtype)
        result = torch.mul(a, b)
        expected = torch.tensor(12, dtype=dtype)
        assert torch.equal(result, expected), f"mul failed for {dtype}"

    def test_eq(self, dtype):
        """Test equality comparison operation (already supported)."""
        a = torch.tensor(5, dtype=dtype)
        b = torch.tensor(5, dtype=dtype)
        result = torch.eq(a, b)
        expected = torch.tensor(True)
        assert torch.equal(result, expected), f"eq failed for {dtype}"

    # =========================================================================
    # Unsupported group: these 3 operators typically do not support uint32/64 (need to be fixed)
    # =========================================================================

    def test_remainder(self, dtype):
        """Test remainder operation (support pending)."""
        a = torch.tensor(10, dtype=dtype)
        b = torch.tensor(3, dtype=dtype)
        result = torch.remainder(a, b)
        expected = torch.tensor(1, dtype=dtype)
        assert torch.equal(result, expected), f"remainder failed for {dtype}"

    def test_gcd(self, dtype):
        """Test GCD (greatest common divisor) operation (support pending)."""
        a = torch.tensor(12, dtype=dtype)
        b = torch.tensor(8, dtype=dtype)
        result = torch.gcd(a, b)
        expected = torch.tensor(4, dtype=dtype)
        assert torch.equal(result, expected), f"gcd failed for {dtype}"

    def test_floor_divide(self, dtype):
        """Test floor_divide operation (support pending)."""
        a = torch.tensor(10, dtype=dtype)
        b = torch.tensor(3, dtype=dtype)
        result = torch.floor_divide(a, b)
        expected = torch.tensor(3, dtype=dtype)
        assert torch.equal(result, expected), f"floor_divide failed for {dtype}"

