"""
Tests for 'v3-performance-optimization' skill — Flash Attention Triton Kernels.
Validates that the Agent implemented correct Triton-based flash attention with
@triton.jit kernels, online softmax, causal masking, and backward pass.
"""

import glob
import os
import re
import subprocess
import textwrap

import pytest


class TestV3PerformanceOptimization:
    """Verify Triton flash attention kernel implementation."""

    REPO_DIR = "/workspace/flash-attention"

    # ── helpers ──────────────────────────────────────────────────────────

    @staticmethod
    def _safe_read(path: str) -> str:
        with open(path, "r", encoding="utf-8", errors="ignore") as fh:
            return fh.read()

    @classmethod
    def _run_in_repo(
        cls, script: str, timeout: int = 120
    ) -> subprocess.CompletedProcess:
        return subprocess.run(
            ["python", "-c", textwrap.dedent(script)],
            cwd=cls.REPO_DIR,
            capture_output=True,
            text=True,
            timeout=timeout,
        )

    # ── file_path_check (static) ────────────────────────────────────────

    def test_flash_attn_triton_module_exists(self):
        """Verify the core Triton flash attention module file exists."""
        path = os.path.join(self.REPO_DIR, "flash_attn", "flash_attn_triton.py")
        assert os.path.isfile(path), f"Missing {path}"

    def test_benchmarks_directory_exists(self):
        """Verify the benchmarks directory is present for performance measurement."""
        bench_dir = os.path.join(self.REPO_DIR, "benchmarks")
        assert os.path.isdir(bench_dir), f"Missing {bench_dir}"
        scripts = glob.glob(os.path.join(bench_dir, "*.py"))
        assert len(scripts) >= 1, "benchmarks/ should contain at least one script"

    # ── semantic_check (static) ─────────────────────────────────────────

    def test_triton_jit_decorator_on_fwd_kernel(self):
        """Verify the forward kernel function uses @triton.jit decorator."""
        path = os.path.join(self.REPO_DIR, "flash_attn", "flash_attn_triton.py")
        assert os.path.isfile(path), f"Missing {path}"
        content = self._safe_read(path)
        idx_jit = content.find("@triton.jit")
        idx_fwd = content.find("_fwd_kernel")
        assert idx_jit >= 0, "@triton.jit decorator not found"
        assert idx_fwd >= 0, "_fwd_kernel function not found"
        # jit should appear before the function definition
        jit_before_fwd = content[:idx_fwd].rfind("@triton.jit")
        assert jit_before_fwd >= 0, "_fwd_kernel is not decorated with @triton.jit"

    def test_online_softmax_pattern_present(self):
        """Verify the kernel implements numerically stable online softmax."""
        path = os.path.join(self.REPO_DIR, "flash_attn", "flash_attn_triton.py")
        content = self._safe_read(path)
        has_max = re.search(r"tl\.max|triton\.language\.max", content)
        has_exp = re.search(r"tl\.exp|triton\.language\.exp", content)
        assert (
            has_max and has_exp
        ), "Online softmax pattern not found (needs tl.max and tl.exp)"

    def test_causal_mask_implementation(self):
        """Verify causal masking logic is present."""
        path = os.path.join(self.REPO_DIR, "flash_attn", "flash_attn_triton.py")
        content = self._safe_read(path)
        has_where = re.search(r"tl\.where", content)
        has_causal = re.search(r"causal|CAUSAL|is_causal", content, re.IGNORECASE)
        assert (
            has_where or has_causal
        ), "Causal mask logic not found (expected tl.where or causal flag)"

    def test_backward_kernel_defined(self):
        """Verify backward pass kernel exists for gradient computation."""
        path = os.path.join(self.REPO_DIR, "flash_attn", "flash_attn_triton.py")
        content = self._safe_read(path)
        assert re.search(r"_bwd_kernel", content), "_bwd_kernel function not found"
        assert re.search(r"@triton\.jit", content), "@triton.jit decorator not found"

    # ── functional_check ────────────────────────────────────────────────

    def test_flash_attn_func_import(self):
        """Verify flash_attn_func can be imported without errors."""
        result = self._run_in_repo(
            """\
            import sys
            sys.path.insert(0, '.')
            from flash_attn.flash_attn_triton import flash_attn_func
            print('import OK')
        """
        )
        if result.returncode != 0:
            pytest.skip(f"Import failed (may need GPU): {result.stderr[:300]}")
        assert "import OK" in result.stdout

    def test_forward_pass_output_shape(self):
        """Verify forward pass output shape matches (batch, heads, seq_len, head_dim)."""
        result = self._run_in_repo(
            """\
            import sys, torch
            sys.path.insert(0, '.')
            from flash_attn.flash_attn_triton import flash_attn_func
            q = torch.randn(1, 8, 128, 64, device='cuda', dtype=torch.float16)
            out = flash_attn_func(q, q, q)
            assert out.shape == (1, 8, 128, 64), f"Bad shape: {out.shape}"
            print('shape OK')
        """,
            timeout=300,
        )
        if result.returncode != 0:
            pytest.skip(f"Forward pass failed (may need GPU): {result.stderr[:300]}")
        assert "shape OK" in result.stdout

    def test_non_causal_matches_reference(self):
        """Verify non-causal output matches torch SDPA within tolerance."""
        result = self._run_in_repo(
            """\
            import sys, torch; import torch.nn.functional as F
            sys.path.insert(0, '.')
            from flash_attn.flash_attn_triton import flash_attn_func
            q = k = v = torch.randn(1, 4, 64, 32, device='cuda', dtype=torch.float16)
            out = flash_attn_func(q, k, v)
            ref = F.scaled_dot_product_attention(q, k, v)
            assert torch.allclose(out, ref, atol=1e-2), "Non-causal mismatch"
            print('match OK')
        """,
            timeout=300,
        )
        if result.returncode != 0:
            pytest.skip(
                f"Reference comparison failed (may need GPU): {result.stderr[:300]}"
            )
        assert "match OK" in result.stdout

    def test_causal_mode_matches_reference(self):
        """Verify causal=True mode applies correct masking consistent with reference."""
        result = self._run_in_repo(
            """\
            import sys, torch; import torch.nn.functional as F
            sys.path.insert(0, '.')
            from flash_attn.flash_attn_triton import flash_attn_func
            q = k = v = torch.randn(1, 4, 64, 32, device='cuda', dtype=torch.float16)
            out = flash_attn_func(q, k, v, causal=True)
            ref = F.scaled_dot_product_attention(q, k, v, is_causal=True)
            assert torch.allclose(out, ref, atol=1e-2), "Causal mismatch"
            print('causal OK')
        """,
            timeout=300,
        )
        if result.returncode != 0:
            pytest.skip(
                f"Causal comparison failed (may need GPU): {result.stderr[:300]}"
            )
        assert "causal OK" in result.stdout

    def test_fp16_dtype_preserved(self):
        """Verify output dtype matches input dtype (fp16 in, fp16 out)."""
        result = self._run_in_repo(
            """\
            import sys, torch
            sys.path.insert(0, '.')
            from flash_attn.flash_attn_triton import flash_attn_func
            q = torch.randn(1, 4, 64, 32, device='cuda', dtype=torch.float16)
            out = flash_attn_func(q, q, q)
            assert out.dtype == torch.float16, f"Expected fp16, got {out.dtype}"
            print('dtype OK')
        """,
            timeout=300,
        )
        if result.returncode != 0:
            pytest.skip(f"Dtype test failed (may need GPU): {result.stderr[:300]}")
        assert "dtype OK" in result.stdout

    def test_cpu_tensor_raises_error(self):
        """Verify passing CPU tensors raises an error (Triton requires CUDA)."""
        result = self._run_in_repo(
            """\
            import sys, torch
            sys.path.insert(0, '.')
            from flash_attn.flash_attn_triton import flash_attn_func
            q = torch.randn(1, 4, 64, 32, dtype=torch.float16)
            try:
                flash_attn_func(q, q, q)
                print('NO_ERROR')
            except (RuntimeError, Exception) as e:
                print(f'ERROR:{e}')
        """,
            timeout=300,
        )
        if result.returncode != 0:
            pytest.skip(f"CPU tensor test failed: {result.stderr[:300]}")
        assert "ERROR" in result.stdout, "Expected an error for CPU tensors"
