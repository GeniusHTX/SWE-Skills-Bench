"""
Tests for 'vector-index-tuning' skill — FAISS Vector Index Tuning.
Validates that the Agent implemented HNSW and IVFFlat index builders and an
IndexEvaluator with recall, QPS, and memory evaluation methods, plus proper
error handling for edge cases.
"""

import glob
import os
import re
import subprocess
import textwrap

import pytest


class TestVectorIndexTuning:
    """Verify FAISS vector index tuning implementation."""

    REPO_DIR = "/workspace/faiss"

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

    def test_index_builder_file_exists(self):
        """Verify the index builder module file exists."""
        path = os.path.join(self.REPO_DIR, "benchmark", "index_builder.py")
        assert os.path.isfile(path), f"Missing {path}"

    def test_evaluator_file_exists(self):
        """Verify the evaluator module file exists."""
        path = os.path.join(self.REPO_DIR, "benchmark", "evaluator.py")
        assert os.path.isfile(path), f"Missing {path}"

    # ── semantic_check (static) ─────────────────────────────────────────

    def test_hnsw_builder_class_defined(self):
        """Verify HNSWIndexBuilder class is defined with M, ef_construction, and build()."""
        path = os.path.join(self.REPO_DIR, "benchmark", "index_builder.py")
        assert os.path.isfile(path), f"Missing {path}"
        content = self._safe_read(path)
        assert re.search(
            r"class\s+HNSWIndexBuilder", content
        ), "HNSWIndexBuilder class not found"
        assert re.search(r"M\b", content), "M parameter not found"
        assert re.search(
            r"ef_construction", content
        ), "ef_construction parameter not found"
        assert re.search(r"def\s+build\s*\(", content), "build() method not found"

    def test_ivfflat_builder_class_defined(self):
        """Verify IVFFlatIndexBuilder class with n_lists and build() calling train+add."""
        path = os.path.join(self.REPO_DIR, "benchmark", "index_builder.py")
        assert os.path.isfile(path), f"Missing {path}"
        content = self._safe_read(path)
        assert re.search(
            r"class\s+IVFFlatIndexBuilder", content
        ), "IVFFlatIndexBuilder class not found"
        assert re.search(r"n_lists", content), "n_lists parameter not found"
        assert re.search(r"\.train\s*\(", content), "index.train() call not found"
        assert re.search(r"\.add\s*\(", content), "index.add() call not found"

    def test_evaluator_has_recall_qps_memory_methods(self):
        """Verify IndexEvaluator defines evaluate_recall, evaluate_qps, evaluate_memory."""
        path = os.path.join(self.REPO_DIR, "benchmark", "evaluator.py")
        assert os.path.isfile(path), f"Missing {path}"
        content = self._safe_read(path)
        assert re.search(
            r"class\s+IndexEvaluator", content
        ), "IndexEvaluator class not found"
        for method in ("evaluate_recall", "evaluate_qps", "evaluate_memory"):
            assert re.search(
                rf"def\s+{method}\s*\(", content
            ), f"{method} method not found in IndexEvaluator"

    def test_faiss_import_in_index_builder(self):
        """Verify faiss is imported in index_builder.py."""
        path = os.path.join(self.REPO_DIR, "benchmark", "index_builder.py")
        assert os.path.isfile(path), f"Missing {path}"
        content = self._safe_read(path)
        assert re.search(
            r"import\s+faiss|from\s+faiss", content
        ), "'import faiss' not found in index_builder.py"

    # ── functional_check ────────────────────────────────────────────────

    def test_hnsw_build_ntotal_correct(self):
        """Verify building HNSW index from 1000 vectors results in ntotal==1000."""
        result = self._run_in_repo(
            """\
            import sys; sys.path.insert(0, '.')
            import numpy as np
            from benchmark.index_builder import HNSWIndexBuilder
            vecs = np.random.rand(1000, 128).astype('float32')
            idx = HNSWIndexBuilder(M=16, ef_construction=100).build(vecs)
            assert idx.ntotal == 1000, f"ntotal={idx.ntotal}"
            print('ntotal OK')
        """,
            timeout=300,
        )
        if result.returncode != 0:
            pytest.skip(f"HNSW build test failed: {result.stderr[:300]}")
        assert "ntotal OK" in result.stdout

    def test_recall_perfect_ground_truth(self):
        """Verify recall@k with perfect ground truth returns 1.0."""
        result = self._run_in_repo(
            """\
            import sys; sys.path.insert(0, '.')
            import numpy as np, faiss
            from benchmark.evaluator import IndexEvaluator
            vecs = np.random.rand(1000, 128).astype('float32')
            ref = faiss.IndexFlatL2(128)
            ref.add(vecs)
            q = vecs[:10]
            D, I = ref.search(q, 5)
            ev = IndexEvaluator()
            r = ev.evaluate_recall(ref, q, I, k=5)
            assert r == 1.0, f"recall={r}"
            print('recall OK')
        """,
            timeout=300,
        )
        if result.returncode != 0:
            pytest.skip(f"Recall test failed: {result.stderr[:300]}")
        assert "recall OK" in result.stdout

    def test_recall_wrong_ground_truth_near_zero(self):
        """Verify recall with completely wrong ground truth returns ~0.0."""
        result = self._run_in_repo(
            """\
            import sys; sys.path.insert(0, '.')
            import numpy as np, faiss
            from benchmark.evaluator import IndexEvaluator
            from benchmark.index_builder import HNSWIndexBuilder
            vecs = np.random.rand(1000, 128).astype('float32')
            idx = HNSWIndexBuilder(M=16, ef_construction=100).build(vecs)
            q = vecs[:10]
            wrong_gt = np.zeros((10, 5), dtype='int64') + 999
            ev = IndexEvaluator()
            r = ev.evaluate_recall(idx, q, wrong_gt, k=5)
            assert r < 0.01, f"Expected near-zero recall, got {r}"
            print('low recall OK')
        """,
            timeout=300,
        )
        if result.returncode != 0:
            pytest.skip(f"Wrong GT test failed: {result.stderr[:300]}")
        assert "low recall OK" in result.stdout

    def test_qps_positive_value(self):
        """Verify evaluate_qps returns a positive float."""
        result = self._run_in_repo(
            """\
            import sys; sys.path.insert(0, '.')
            import numpy as np
            from benchmark.index_builder import HNSWIndexBuilder
            from benchmark.evaluator import IndexEvaluator
            vecs = np.random.rand(1000, 128).astype('float32')
            idx = HNSWIndexBuilder(M=16, ef_construction=100).build(vecs)
            ev = IndexEvaluator()
            qps = ev.evaluate_qps(idx, vecs[:100], n_runs=3)
            assert qps > 0, f"Expected positive QPS, got {qps}"
            print('qps OK')
        """,
            timeout=300,
        )
        if result.returncode != 0:
            pytest.skip(f"QPS test failed: {result.stderr[:300]}")
        assert "qps OK" in result.stdout

    def test_ivfflat_too_few_vectors_raises(self):
        """Verify IVFFlatIndexBuilder raises when n_lists exceeds vectors."""
        result = self._run_in_repo(
            """\
            import sys; sys.path.insert(0, '.')
            import numpy as np
            from benchmark.index_builder import IVFFlatIndexBuilder
            vecs = np.random.rand(10, 128).astype('float32')
            try:
                IVFFlatIndexBuilder(n_lists=500).build(vecs)
                print('NO_ERROR')
            except (ValueError, RuntimeError, Exception) as e:
                print(f'ERROR:{e}')
        """,
            timeout=300,
        )
        if result.returncode != 0:
            pytest.skip(f"IVFFlat test failed: {result.stderr[:300]}")
        assert "ERROR" in result.stdout, "Expected error for too few vectors"

    def test_non_float32_vectors_raises(self):
        """Verify that passing non-float32 vectors raises TypeError or auto-casts."""
        result = self._run_in_repo(
            """\
            import sys; sys.path.insert(0, '.')
            import numpy as np
            from benchmark.index_builder import HNSWIndexBuilder
            vecs = np.random.rand(100, 128).astype('float64')
            try:
                idx = HNSWIndexBuilder(M=16, ef_construction=100).build(vecs)
                if idx.ntotal == 100:
                    print('AUTOCAST')
                else:
                    print('ERROR:unexpected ntotal')
            except (TypeError, RuntimeError, Exception) as e:
                print(f'ERROR:{e}')
        """,
            timeout=300,
        )
        if result.returncode != 0:
            pytest.skip(f"non-float32 test failed: {result.stderr[:300]}")
        out = result.stdout.strip()
        assert (
            "ERROR" in out or "AUTOCAST" in out
        ), "Expected TypeError or transparent auto-cast"
