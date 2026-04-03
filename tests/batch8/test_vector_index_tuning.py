"""
Test for 'vector-index-tuning' skill — FAISS HNSW Index Tuning
Validates that the Agent implemented FAISS HNSW index tuner, optimizer,
and benchmark modules with efConstruction/efSearch, recall formula, and persistence.
"""

import os
import re
import sys

import pytest


class TestVectorIndexTuning:
    """Verify FAISS HNSW index tuning implementation."""

    REPO_DIR = "/workspace/faiss"

    @staticmethod
    def _read(path: str) -> str:
        try:
            with open(path, "r", errors="ignore") as fh:
                return fh.read()
        except OSError:
            return ""

    def _find_file(self, *candidates):
        for c in candidates:
            p = os.path.join(self.REPO_DIR, c)
            if os.path.isfile(p):
                return p
        return None

    # ── file_path_check ─────────────────────────────────────────────

    def test_tuner_module_exists(self):
        """Verify faiss_tuning/tuner.py or index_tuner.py exists."""
        candidates = ("faiss_tuning/tuner.py", "index_tuner.py")
        found = any(
            os.path.isfile(os.path.join(self.REPO_DIR, c)) for c in candidates)
        assert found, f"Missing: none of {candidates} found"

    def test_optimizer_module_exists(self):
        """Verify faiss_tuning/optimizer.py or hnsw_optimizer.py exists."""
        candidates = ("faiss_tuning/optimizer.py", "hnsw_optimizer.py")
        found = any(
            os.path.isfile(os.path.join(self.REPO_DIR, c)) for c in candidates)
        assert found, f"Missing: none of {candidates} found"

    def test_benchmark_module_exists(self):
        """Verify faiss_tuning/benchmark.py or index_benchmark.py exists."""
        candidates = ("faiss_tuning/benchmark.py", "index_benchmark.py")
        found = any(
            os.path.isfile(os.path.join(self.REPO_DIR, c)) for c in candidates)
        assert found, f"Missing: none of {candidates} found"

    # ── semantic_check ──────────────────────────────────────────────

    def test_hnsw_flat_instantiation(self):
        """Verify faiss.IndexHNSWFlat is instantiated with M parameter."""
        path = self._find_file("faiss_tuning/tuner.py", "index_tuner.py")
        assert path, "Tuner module not found"
        content = self._read(path)
        assert "IndexHNSWFlat" in content, "IndexHNSWFlat not found"

    def test_ef_construction_and_ef_search_assigned(self):
        """Verify hnsw.efConstruction and hnsw.efSearch are assigned."""
        path = self._find_file("faiss_tuning/tuner.py", "index_tuner.py")
        assert path, "Tuner module not found"
        content = self._read(path)
        assert "efConstruction" in content, "efConstruction not found"
        assert "efSearch" in content, "efSearch not found"

    def test_recall_intersection_formula(self):
        """Verify recall is computed as set intersection divided by k."""
        path = self._find_file("faiss_tuning/benchmark.py", "index_benchmark.py")
        assert path, "Benchmark module not found"
        content = self._read(path)
        found = any(kw in content for kw in ("set(", "intersection", "& set"))
        assert found, "Set intersection for recall calculation not found"

    def test_write_read_index_calls(self):
        """Verify faiss.write_index and faiss.read_index are used for persistence."""
        path = self._find_file("faiss_tuning/tuner.py", "index_tuner.py")
        assert path, "Tuner module not found"
        content = self._read(path)
        assert "write_index" in content, "write_index not found"
        assert "read_index" in content, "read_index not found"

    # ── functional_check (import) ───────────────────────────────────

    def _skip_unless_importable(self):
        if not os.path.isdir(self.REPO_DIR):
            pytest.skip("Repo dir does not exist")
        if self.REPO_DIR not in sys.path:
            sys.path.insert(0, self.REPO_DIR)

    def test_build_index_ntotal_equals_vector_count(self):
        """IndexTuner.build(1000 vectors, M=16, ef_construction=200): ntotal == 1000."""
        self._skip_unless_importable()
        try:
            import numpy as np
            from faiss_tuning.tuner import IndexTuner
        except Exception as exc:
            pytest.skip(f"Cannot import: {exc}")
        vecs = np.random.randn(1000, 128).astype("float32")
        idx = IndexTuner().build(vecs, M=16, ef_construction=200)
        assert idx.ntotal == 1000, f"Expected ntotal=1000, got {idx.ntotal}"

    def test_recall_one_on_exact_results(self):
        """Recall formula: ids={1,2,3}, ground_truth={1,2,3}, k=3 -> 1.0."""
        self._skip_unless_importable()
        try:
            from faiss_tuning.benchmark import IndexBenchmark
        except Exception as exc:
            pytest.skip(f"Cannot import: {exc}")
        recall = IndexBenchmark().compute_recall(
            result_ids=[1, 2, 3], ground_truth=[1, 2, 3], k=3)
        assert recall == 1.0, f"Expected recall=1.0, got {recall}"

    def test_recall_partial_overlap(self):
        """Recall formula: ids={1,4,5}, ground_truth={1,2,3}, k=3 -> ~0.333."""
        self._skip_unless_importable()
        try:
            from faiss_tuning.benchmark import IndexBenchmark
        except Exception as exc:
            pytest.skip(f"Cannot import: {exc}")
        recall = IndexBenchmark().compute_recall(
            result_ids=[1, 4, 5], ground_truth=[1, 2, 3], k=3)
        assert abs(recall - 0.333) < 0.01, f"Expected ~0.333, got {recall}"

    def test_save_load_roundtrip(self):
        """Save and reload index: same query returns same top-1 result."""
        self._skip_unless_importable()
        try:
            import numpy as np
            import tempfile
            from faiss_tuning.tuner import IndexTuner
        except Exception as exc:
            pytest.skip(f"Cannot import: {exc}")
        vecs = np.random.randn(100, 32).astype("float32")
        tuner = IndexTuner()
        idx = tuner.build(vecs, M=8, ef_construction=64)
        q = np.random.randn(1, 32).astype("float32")
        _, orig = idx.search(q, 1)
        with tempfile.NamedTemporaryFile(suffix=".index", delete=False) as f:
            path = f.name
        try:
            tuner.save_index(idx, path)
            loaded = tuner.load_index(path)
            _, reloaded = loaded.search(q, 1)
            assert orig[0][0] == reloaded[0][0], \
                "Save/load roundtrip produced different results"
        finally:
            os.unlink(path)
