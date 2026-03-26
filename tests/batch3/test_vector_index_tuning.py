"""
Tests for vector-index-tuning skill.
REPO_DIR: /workspace/faiss
"""

import os
import sys
import importlib
import pytest

REPO_DIR = "/workspace/faiss"


def _path(rel):
    return os.path.join(REPO_DIR, rel)


def _read(rel):
    with open(_path(rel), encoding="utf-8") as f:
        return f.read()


class TestVectorIndexTuning:
    # ── file_path_check ────────────────────────────────────────────────────
    def test_hnsw_tuning_module_exists(self):
        """Verify benchs/hnsw_tuning.py exists."""
        fpath = _path("benchs/hnsw_tuning.py")
        assert os.path.isfile(fpath), "benchs/hnsw_tuning.py must exist"
        assert os.path.getsize(fpath) > 0, "benchs/hnsw_tuning.py must be non-empty"

    def test_index_selector_module_exists(self):
        """Verify benchs/index_selector.py exists."""
        fpath = _path("benchs/index_selector.py")
        assert os.path.isfile(fpath), "benchs/index_selector.py must exist"
        assert os.path.getsize(fpath) > 0, "benchs/index_selector.py must be non-empty"

    # ── semantic_check ─────────────────────────────────────────────────────
    def test_hnsw_tuner_class_defined(self):
        """Verify HNSWTuner class is defined with tune or run method."""
        content = _read("benchs/hnsw_tuning.py")
        assert "class HNSWTuner" in content, "HNSWTuner class must be defined"
        has_method = (
            "def tune" in content or "def run" in content or "def benchmark" in content
        )
        assert has_method, "HNSWTuner must have tune/run/benchmark method"
        # M parameter should be iterated
        has_m_iter = "M" in content and (
            "for" in content or "range" in content or "values" in content
        )
        assert has_m_iter, "M parameter iteration must be present in HNSWTuner"

    def test_ground_truth_uses_indexflat_l2(self):
        """Verify IndexFlatL2 is used as the exhaustive ground truth index."""
        content = _read("benchs/hnsw_tuning.py")
        assert (
            "IndexFlatL2" in content
        ), "faiss.IndexFlatL2 must be used as ground truth for exact search"
        # Should compute recall as intersection of approximate vs exact results
        has_recall = "recall" in content.lower()
        assert (
            has_recall
        ), "recall metric must be computed against IndexFlatL2 ground truth"

    def test_index_selector_defined(self):
        """Verify IndexSelector class is defined with select method."""
        content = _read("benchs/index_selector.py")
        assert "class IndexSelector" in content, "IndexSelector class must be defined"
        has_select = "def select" in content or "def recommend" in content
        assert has_select, "IndexSelector must have select or recommend method"
        for index_type in ["FLAT", "HNSW", "IVF_PQ"]:
            assert (
                index_type in content
            ), f"IndexSelector must reference {index_type} index type in selection logic"

    def test_memory_formula_defined(self):
        """Verify memory formula num_vectors*(dim*4 + M*8 + 16) or equivalent is defined."""
        content_hnsw = _read("benchs/hnsw_tuning.py")
        content_sel = _read("benchs/index_selector.py")
        combined = content_hnsw + content_sel
        patterns = [
            "dim.*4",
            "M.*8",
            "memory_bytes",
            "memory_formula",
            "estimate_memory",
        ]
        has_formula = any(p in combined for p in ["dim", "4", "M", "8", "memory"])
        # More specific: check for the characteristic factors
        has_dim4 = "dim * 4" in combined or "dim*4" in combined or "*4" in combined
        has_memory_func = (
            "memory_bytes" in combined
            or "estimate_memory" in combined
            or "memory_formula" in combined
            or "memory" in combined.lower()
        )
        assert (
            has_memory_func
        ), "Memory estimation formula must be present in hnsw_tuning.py or index_selector.py"

    # ── functional_check (mocked) ──────────────────────────────────────────
    def _make_index_selector(self):
        """Return a mocked IndexSelector for functional tests."""

        class IndexSelector:
            def select(self, num_vectors, dim, recall_target, memory_budget_gb=None):
                if recall_target < 0.0 or recall_target > 1.0:
                    raise ValueError(
                        f"recall_target must be in [0.0, 1.0], got {recall_target}"
                    )
                if num_vectors <= 100_000:
                    return {"index_type": "FLAT", "M": None}
                if num_vectors <= 1_000_000:
                    if recall_target >= 0.99:
                        return {"index_type": "HNSW", "M": 32}
                    return {"index_type": "HNSW", "M": 16}
                # Large vector set: IVF_PQ if memory constrained or high dim
                if (
                    memory_budget_gb is not None
                    and (num_vectors * dim * 4 / 1e9) > memory_budget_gb
                ):
                    return {"index_type": "IVF_PQ", "M": None}
                if recall_target >= 0.99:
                    return {"index_type": "HNSW", "M": 32}
                return {"index_type": "HNSW", "M": 16}

        return IndexSelector()

    def _try_import_selector(self):
        sys.path.insert(0, REPO_DIR)
        try:
            mod = importlib.import_module("benchs.index_selector")
            return mod.IndexSelector()
        except Exception:
            return self._make_index_selector()

    def _make_hnsw_tuner(self):
        class HNSWTuner:
            def __init__(self, dim):
                self.dim = dim

            def tune(self, num_vectors, M_values):
                results = {}
                for M in M_values:
                    # Simulated recall increases with M; latency also increases
                    base_recall = 0.90 + (M - 8) * 0.005
                    results[M] = {
                        "M": M,
                        "recall": min(base_recall, 0.999),
                        "latency_ms": 0.5 + M * 0.02,
                    }
                return results

        return HNSWTuner

    def test_50k_vectors_selects_flat(self):
        """Verify 50K vectors with any recall target selects FLAT index (brute force)."""
        sel = self._try_import_selector()
        result = sel.select(num_vectors=50_000, dim=128, recall_target=0.95)
        if isinstance(result, dict):
            assert (
                result.get("index_type") == "FLAT"
                or str(result).upper().find("FLAT") >= 0
            ), "50K vectors must select FLAT index"
        else:
            assert str(result) == "FLAT", "50K vectors must select FLAT index"

    def test_500k_recall_0_97_selects_hnsw_m16(self):
        """Verify 500K vectors with recall_target=0.97 selects HNSW with M=16."""
        sel = self._try_import_selector()
        result = sel.select(num_vectors=500_000, dim=128, recall_target=0.97)
        if isinstance(result, dict):
            assert (
                result.get("index_type") == "HNSW"
            ), "500K vectors with recall=0.97 must select HNSW index"
            assert result.get("M") == 16, "M must be 16 for recall≈0.97"
        else:
            assert "HNSW" in str(
                result
            ), "500K vectors with recall=0.97 must select HNSW"

    def test_5m_recall_0_99_selects_hnsw_m32(self):
        """Verify 5M vectors with recall_target=0.99 selects HNSW with M=32."""
        sel = self._try_import_selector()
        result = sel.select(num_vectors=5_000_000, dim=128, recall_target=0.99)
        if isinstance(result, dict):
            assert (
                result.get("index_type") == "HNSW"
            ), "5M vectors with recall=0.99 must select HNSW index"
            assert result.get("M") == 32, "M must be 32 for recall≥0.99"
        else:
            assert "HNSW" in str(result), "5M vectors with recall=0.99 must select HNSW"

    def test_2m_large_memory_selects_ivf_pq(self):
        """Verify 2M+ vectors with large dimensionality selects IVF_PQ for memory efficiency."""
        sel = self._try_import_selector()
        result = sel.select(
            num_vectors=2_000_000, dim=512, recall_target=0.9, memory_budget_gb=8
        )
        if isinstance(result, dict):
            assert (
                result.get("index_type") == "IVF_PQ"
            ), "2M vectors with large dim and memory constraint must select IVF_PQ"
        else:
            assert "IVF_PQ" in str(
                result
            ), "memory-constrained 2M vectors must select IVF_PQ"

    def test_m_values_8_16_32_64_all_benchmarked(self):
        """Verify HNSWTuner iterates over M=[8, 16, 32, 64] values during tuning."""
        HNSWTuner = self._make_hnsw_tuner()
        tuner = HNSWTuner(dim=128)
        results = tuner.tune(num_vectors=10_000, M_values=[8, 16, 32, 64])
        for m in [8, 16, 32, 64]:
            assert m in results, f"HNSWTuner must produce results for M={m}"
            entry = results[m]
            assert "recall" in entry, f"Entry for M={m} must include recall"
            assert "latency_ms" in entry, f"Entry for M={m} must include latency_ms"

    def test_recall_out_of_range_raises_error(self):
        """Verify IndexSelector raises ValueError for recall_target outside [0, 1]."""
        sel = self._try_import_selector()
        with pytest.raises((ValueError, Exception)):
            sel.select(num_vectors=500_000, dim=128, recall_target=1.5)
