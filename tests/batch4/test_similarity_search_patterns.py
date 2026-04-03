"""
Test for 'similarity-search-patterns' skill — Similarity Search Patterns
Validates SimilarityEngine, IndexAdvisor, and BatchSearcher implementations in Milvus.
"""

import os
import re
import ast
import sys
import glob
import pytest


class TestSimilaritySearchPatterns:
    """Tests for similarity search patterns in the milvus repo."""

    REPO_DIR = "/workspace/milvus"

    def _read(self, relpath):
        full = os.path.join(self.REPO_DIR, relpath)
        with open(full, "r", errors="ignore") as f:
            return f.read()

    # --- File Path Checks ---

    def test_engine_py_exists(self):
        """Verifies that scripts/similarity_engine/engine.py exists."""
        path = os.path.join(self.REPO_DIR, "scripts", "similarity_engine", "engine.py")
        assert os.path.exists(path), f"Expected file not found: {path}"

    def test_index_advisor_py_exists(self):
        """Verifies that scripts/similarity_engine/index_advisor.py exists."""
        path = os.path.join(
            self.REPO_DIR, "scripts", "similarity_engine", "index_advisor.py"
        )
        assert os.path.exists(path), f"Expected file not found: {path}"

    def test_batch_search_py_exists(self):
        """Verifies that scripts/similarity_engine/batch_search.py exists."""
        path = os.path.join(
            self.REPO_DIR, "scripts", "similarity_engine", "batch_search.py"
        )
        assert os.path.exists(path), f"Expected file not found: {path}"

    def test_init_py_exists(self):
        """Verifies that scripts/similarity_engine/__init__.py exists."""
        path = os.path.join(
            self.REPO_DIR, "scripts", "similarity_engine", "__init__.py"
        )
        assert os.path.exists(path), f"Expected file not found: {path}"

    # --- Semantic Checks (static) ---

    def test_sem_similarity_engine_class_defined(self):
        """SimilarityEngine class is defined in engine.py."""
        content = self._read("scripts/similarity_engine/engine.py")
        assert re.search(
            r"class\s+SimilarityEngine", content
        ), "class SimilarityEngine not found"

    def test_sem_similarity_engine_methods(self):
        """SimilarityEngine has insert, search, hybrid_search, delete, count methods."""
        content = self._read("scripts/similarity_engine/engine.py")
        for method in ["insert", "search", "hybrid_search", "delete", "count"]:
            assert re.search(
                rf"def\s+{method}\s*\(", content
            ), f"Method {method} not found"

    def test_sem_index_advisor_class_defined(self):
        """IndexAdvisor class is defined in index_advisor.py."""
        content = self._read("scripts/similarity_engine/index_advisor.py")
        assert re.search(
            r"class\s+IndexAdvisor", content
        ), "class IndexAdvisor not found"

    def test_sem_index_advisor_has_recommend(self):
        """IndexAdvisor has recommend method."""
        content = self._read("scripts/similarity_engine/index_advisor.py")
        assert re.search(r"def\s+recommend\s*\(", content), "recommend method not found"

    def test_sem_batch_searcher_class_defined(self):
        """BatchSearcher class is defined in batch_search.py."""
        content = self._read("scripts/similarity_engine/batch_search.py")
        assert re.search(
            r"class\s+BatchSearcher", content
        ), "class BatchSearcher not found"

    def test_sem_similarity_engine_constructor_params(self):
        """SimilarityEngine constructor takes dimension and metric_type parameters."""
        content = self._read("scripts/similarity_engine/engine.py")
        assert "dimension" in content, "dimension parameter not found"
        assert "metric_type" in content, "metric_type parameter not found"

    # --- Functional Checks (import) ---

    def test_func_import_similarity_engine(self):
        """SimilarityEngine is importable."""
        old_path = sys.path[:]
        sys.path.insert(0, os.path.join(self.REPO_DIR, "scripts"))
        try:
            from similarity_engine.engine import SimilarityEngine

            assert SimilarityEngine is not None
        finally:
            sys.path[:] = old_path

    def test_func_import_index_advisor(self):
        """IndexAdvisor is importable."""
        old_path = sys.path[:]
        sys.path.insert(0, os.path.join(self.REPO_DIR, "scripts"))
        try:
            from similarity_engine.index_advisor import IndexAdvisor

            assert IndexAdvisor is not None
        finally:
            sys.path[:] = old_path

    def test_func_similarity_engine_insert_and_count(self):
        """SimilarityEngine insert data and count returns correct count."""
        old_path = sys.path[:]
        sys.path.insert(0, os.path.join(self.REPO_DIR, "scripts"))
        try:
            from similarity_engine.engine import SimilarityEngine

            engine = SimilarityEngine(dimension=32, metric_type="L2")
            vectors = [[1.0] * 32 for _ in range(5)]
            engine.insert(vectors)
            assert engine.count() == 5, f"Expected 5, got {engine.count()}"
        finally:
            sys.path[:] = old_path

    def test_func_similarity_engine_search(self):
        """SimilarityEngine search returns results."""
        old_path = sys.path[:]
        sys.path.insert(0, os.path.join(self.REPO_DIR, "scripts"))
        try:
            from similarity_engine.engine import SimilarityEngine

            engine = SimilarityEngine(dimension=32, metric_type="L2")
            vectors = [[float(i)] * 32 for i in range(5)]
            engine.insert(vectors)
            query = [0.0] * 32
            results = engine.search(query, top_k=3)
            assert len(results) <= 3, f"Expected at most 3 results, got {len(results)}"
        finally:
            sys.path[:] = old_path

    def test_func_similarity_engine_delete(self):
        """SimilarityEngine delete reduces count."""
        old_path = sys.path[:]
        sys.path.insert(0, os.path.join(self.REPO_DIR, "scripts"))
        try:
            from similarity_engine.engine import SimilarityEngine

            engine = SimilarityEngine(dimension=32, metric_type="L2")
            vectors = [[float(i)] * 32 for i in range(5)]
            engine.insert(vectors)
            initial_count = engine.count()
            engine.delete([0])
            assert engine.count() < initial_count, "Count did not decrease after delete"
        finally:
            sys.path[:] = old_path

    def test_func_index_advisor_recommend_flat_for_small(self):
        """IndexAdvisor recommends FLAT for small datasets (~500 vectors)."""
        old_path = sys.path[:]
        sys.path.insert(0, os.path.join(self.REPO_DIR, "scripts"))
        try:
            from similarity_engine.index_advisor import IndexAdvisor

            advisor = IndexAdvisor()
            recommendation = advisor.recommend(num_vectors=500)
            assert (
                recommendation == "FLAT"
            ), f"Expected FLAT for 500 vectors, got {recommendation}"
        finally:
            sys.path[:] = old_path

    def test_func_index_advisor_recommend_hnsw_for_mid(self):
        """IndexAdvisor recommends HNSW for medium datasets (~500,000 vectors)."""
        old_path = sys.path[:]
        sys.path.insert(0, os.path.join(self.REPO_DIR, "scripts"))
        try:
            from similarity_engine.index_advisor import IndexAdvisor

            advisor = IndexAdvisor()
            recommendation = advisor.recommend(num_vectors=500_000)
            assert (
                recommendation == "HNSW"
            ), f"Expected HNSW for 500k vectors, got {recommendation}"
        finally:
            sys.path[:] = old_path

    def test_func_index_advisor_recommend_ivf_pq_for_large(self):
        """IndexAdvisor recommends IVF_PQ for large datasets (~5,000,000 vectors)."""
        old_path = sys.path[:]
        sys.path.insert(0, os.path.join(self.REPO_DIR, "scripts"))
        try:
            from similarity_engine.index_advisor import IndexAdvisor

            advisor = IndexAdvisor()
            recommendation = advisor.recommend(num_vectors=5_000_000)
            assert (
                recommendation == "IVF_PQ"
            ), f"Expected IVF_PQ for 5M vectors, got {recommendation}"
        finally:
            sys.path[:] = old_path

    def test_func_wrong_dimension_insert_raises_error(self):
        """Inserting vectors with wrong dimension raises ValueError."""
        old_path = sys.path[:]
        sys.path.insert(0, os.path.join(self.REPO_DIR, "scripts"))
        try:
            from similarity_engine.engine import SimilarityEngine

            engine = SimilarityEngine(dimension=32, metric_type="L2")
            wrong_vectors = [[1.0] * 64]  # wrong dimension
            with pytest.raises(ValueError):
                engine.insert(wrong_vectors)
        finally:
            sys.path[:] = old_path
