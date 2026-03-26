"""
Test for 'v3-performance-optimization' skill — Flash Attention Sliding Window
Validates that the Agent created flash_attn/flash_attn_sliding_window.py and
modified flash_attn/flash_attn_interface.py to support configurable sliding
window attention with correct interface, edge case handling, and causal mode.
"""

import os
import re
import subprocess
import sys

import pytest


class TestV3PerformanceOptimization:
    """Verify Flash Attention sliding window implementation."""

    REPO_DIR = "/workspace/flash-attention"

    def _read(self, *parts):
        fpath = os.path.join(self.REPO_DIR, *parts)
        assert os.path.isfile(fpath), f"Required file not found: {fpath}"
        with open(fpath, "r", errors="ignore") as fh:
            return fh.read()

    # ------------------------------------------------------------------
    # L1: File existence
    # ------------------------------------------------------------------

    def test_sliding_window_file_exists(self):
        """flash_attn/flash_attn_sliding_window.py must exist."""
        assert os.path.isfile(
            os.path.join(self.REPO_DIR, "flash_attn", "flash_attn_sliding_window.py")
        )

    def test_interface_file_exists(self):
        """flash_attn/flash_attn_interface.py must exist."""
        assert os.path.isfile(
            os.path.join(self.REPO_DIR, "flash_attn", "flash_attn_interface.py")
        )

    # ------------------------------------------------------------------
    # L1: Valid Python syntax
    # ------------------------------------------------------------------

    def test_sliding_window_valid_python(self):
        """flash_attn_sliding_window.py must be syntactically valid."""
        result = subprocess.run(
            ["python3", "-m", "py_compile", "flash_attn/flash_attn_sliding_window.py"],
            cwd=self.REPO_DIR,
            capture_output=True,
            text=True,
            timeout=30,
        )
        assert result.returncode == 0, f"Syntax error:\n{result.stderr}"

    def test_interface_valid_python(self):
        """flash_attn_interface.py must be syntactically valid."""
        result = subprocess.run(
            ["python3", "-m", "py_compile", "flash_attn/flash_attn_interface.py"],
            cwd=self.REPO_DIR,
            capture_output=True,
            text=True,
            timeout=30,
        )
        assert result.returncode == 0, f"Syntax error:\n{result.stderr}"

    # ------------------------------------------------------------------
    # L2: Window size parameter
    # ------------------------------------------------------------------

    def test_window_size_parameter(self):
        """Sliding window module must accept a window_size parameter."""
        content = self._read("flash_attn", "flash_attn_sliding_window.py")
        assert re.search(r"window_size", content), "No window_size parameter found"

    def test_interface_exposes_window_size(self):
        """flash_attn_interface.py must expose window_size parameter."""
        content = self._read("flash_attn", "flash_attn_interface.py")
        assert re.search(
            r"window_size", content
        ), "flash_attn_interface.py does not expose window_size"

    # ------------------------------------------------------------------
    # L2: Full attention fallback
    # ------------------------------------------------------------------

    def test_full_attention_fallback(self):
        """When window_size is None or -1, should fall back to full attention."""
        content = self._read("flash_attn", "flash_attn_sliding_window.py")
        patterns = [
            r"window_size\s*(is\s+None|==\s*None|is\s+not\s+None)",
            r"window_size\s*==\s*-1",
            r"window_size.*None",
            r"None.*window_size",
        ]
        assert any(
            re.search(p, content) for p in patterns
        ), "No full attention fallback when window_size is None or -1"

    # ------------------------------------------------------------------
    # L2: Causal mode support
    # ------------------------------------------------------------------

    def test_causal_mode_support(self):
        """Implementation must support causal mode."""
        content = self._read("flash_attn", "flash_attn_sliding_window.py")
        assert re.search(
            r"causal", content, re.IGNORECASE
        ), "No causal mode support found"

    # ------------------------------------------------------------------
    # L2: Input tensor handling
    # ------------------------------------------------------------------

    def test_accepts_qkv_tensors(self):
        """Must accept query, key, value tensors."""
        content = self._read("flash_attn", "flash_attn_sliding_window.py")
        # Should reference q, k, v or query, key, value
        has_q = re.search(r"\bq\b|\bquery\b", content, re.IGNORECASE)
        has_k = re.search(r"\bk\b|\bkey\b", content, re.IGNORECASE)
        has_v = re.search(r"\bv\b|\bvalue\b", content, re.IGNORECASE)
        assert has_q and has_k and has_v, "Must accept query, key, and value tensors"

    # ------------------------------------------------------------------
    # L2: Window masking logic
    # ------------------------------------------------------------------

    def test_window_masking(self):
        """Implementation must mask tokens outside the sliding window."""
        content = self._read("flash_attn", "flash_attn_sliding_window.py")
        patterns = [
            r"mask",
            r"window",
            r"attend",
            r"-?\s*float\s*\(\s*['\"]inf['\"]\s*\)",
            r"torch\.finfo",
        ]
        found = sum(1 for p in patterns if re.search(p, content, re.IGNORECASE))
        assert (
            found >= 2
        ), "Insufficient window masking logic (need mask + window references)"

    # ------------------------------------------------------------------
    # L2: Edge cases
    # ------------------------------------------------------------------

    def test_edge_case_large_window(self):
        """Should handle window_size >= seq_len (equivalent to full attention)."""
        content = self._read("flash_attn", "flash_attn_sliding_window.py")
        patterns = [
            r"seq_len|seqlen|sequence_length",
            r"min\(",
            r"window_size\s*>=",
            r"window_size\s*>",
        ]
        assert any(
            re.search(p, content) for p in patterns
        ), "No handling for window_size >= sequence length"

    def test_edge_case_window_one(self):
        """Should handle window_size=1 (self-only attention)."""
        content = self._read("flash_attn", "flash_attn_sliding_window.py")
        # Window size 1 should be a valid input; check the function
        # accepts integer window_size
        assert re.search(
            r"(int|window_size)", content
        ), "window_size should accept integer values including 1"

    # ------------------------------------------------------------------
    # L2: Integration with existing API
    # ------------------------------------------------------------------

    def test_interface_imports_sliding_window(self):
        """flash_attn_interface.py should import or reference sliding window."""
        content = self._read("flash_attn", "flash_attn_interface.py")
        patterns = [
            r"sliding_window",
            r"from.*flash_attn_sliding_window",
            r"import.*sliding",
            r"window_size",
        ]
        assert any(
            re.search(p, content) for p in patterns
        ), "flash_attn_interface.py does not integrate sliding window"

    def test_function_definition(self):
        """Sliding window module should define callable functions."""
        content = self._read("flash_attn", "flash_attn_sliding_window.py")
        assert re.search(
            r"def\s+\w+.*window", content, re.IGNORECASE
        ), "No function with 'window' in name found"
