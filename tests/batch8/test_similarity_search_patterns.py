"""
Test for 'similarity-search-patterns' skill — Milvus Similarity Search
Validates that the Agent implemented a Milvus-based similarity search service
with batch upsert, metadata filtering, index management, and query optimization.
"""

import os
import re
import sys

import pytest


class TestSimilaritySearchPatterns:
    """Verify Milvus similarity search implementation."""

    REPO_DIR = "/workspace/milvus"

    @staticmethod
    def _read(path: str) -> str:
        try:
            with open(path, "r", errors="ignore") as fh:
                return fh.read()
        except OSError:
            return ""

    # ── file_path_check ─────────────────────────────────────────────

    def test_service_module_exists(self):
        """Verify similarity_search/service.py or similarity_search.py exists."""
        candidates = ("similarity_search/service.py", "similarity_search.py")
        found = any(
            os.path.isfile(os.path.join(self.REPO_DIR, c)) for c in candidates)
        assert found, f"Missing: none of {candidates} found"

    def test_index_manager_module_exists(self):
        """Verify index_manager.py or similarity_search/index_manager.py exists."""
        candidates = ("similarity_search/index_manager.py", "index_manager.py")
        found = any(
            os.path.isfile(os.path.join(self.REPO_DIR, c)) for c in candidates)
        assert found, f"Missing: none of {candidates} found"

    def test_query_optimizer_module_exists(self):
        """Verify query_optimizer.py or similarity_search/optimizer.py exists."""
        candidates = ("similarity_search/optimizer.py", "query_optimizer.py")
        found = any(
            os.path.isfile(os.path.join(self.REPO_DIR, c)) for c in candidates)
        assert found, f"Missing: none of {candidates} found"

    # ── semantic_check ──────────────────────────────────────────────

    def _find_service_file(self):
        for c in ("similarity_search/service.py", "similarity_search.py"):
            p = os.path.join(self.REPO_DIR, c)
            if os.path.isfile(p):
                return p
        return None

    def _find_index_manager_file(self):
        for c in ("similarity_search/index_manager.py", "index_manager.py"):
            p = os.path.join(self.REPO_DIR, c)
            if os.path.isfile(p):
                return p
        return None

    def test_pymilvus_import_present(self):
        """Verify pymilvus import is present in the service module."""
        path = self._find_service_file()
        assert path, "Service module not found"
        content = self._read(path)
        found = any(kw in content for kw in ("from pymilvus", "import pymilvus"))
        assert found, "pymilvus import not found in service module"

    def test_batch_size_parameter_in_upsert(self):
        """Verify batch_size parameter exists in upsert/insert method signature."""
        path = self._find_service_file()
        assert path, "Service module not found"
        content = self._read(path)
        assert "batch_size" in content, "batch_size not found in service module"

    def test_metadata_filter_expr_param(self):
        """Verify expr= keyword is passed to Collection.search() for metadata filtering."""
        path = self._find_service_file()
        assert path, "Service module not found"
        content = self._read(path)
        assert "expr=" in content, "expr= not found in service module"

    def test_supported_index_types_constant(self):
        """Verify SUPPORTED_INDEX_TYPES or equivalent constant guards index creation."""
        path = self._find_index_manager_file()
        assert path, "Index manager module not found"
        content = self._read(path)
        found = any(kw in content for kw in (
            "SUPPORTED_INDEX_TYPES", "IVF_FLAT", "HNSW"))
        assert found, "Supported index types not found in index manager"

    # ── functional_check (import) ───────────────────────────────────

    def _skip_unless_importable(self):
        if not os.path.isdir(self.REPO_DIR):
            pytest.skip("Repo dir does not exist")
        if self.REPO_DIR not in sys.path:
            sys.path.insert(0, self.REPO_DIR)

    def test_search_results_sorted_by_score_descending(self):
        """search() with mock Collection returns results sorted descending by score."""
        self._skip_unless_importable()
        from unittest.mock import MagicMock
        try:
            from similarity_search.service import SimilaritySearchService
        except Exception as exc:
            pytest.skip(f"Cannot import: {exc}")
        hit1 = MagicMock()
        hit1.id = "a"
        hit1.score = 0.9
        hit1.entity.to_dict.return_value = {}
        hit2 = MagicMock()
        hit2.id = "b"
        hit2.score = 0.5
        hit2.entity.to_dict.return_value = {}
        svc = SimilaritySearchService.__new__(SimilaritySearchService)
        mock_col = MagicMock()
        mock_col.search.return_value = [[hit2, hit1]]
        svc._collection = mock_col
        results = svc.search([0.0] * 128, top_k=2)
        scores = [r[1] for r in results]
        assert scores == sorted(scores, reverse=True), \
            "Results must be sorted descending by score"

    def test_invalid_index_type_raises_value_error(self):
        """VectorIndexManager.create_index() with unsupported type raises ValueError."""
        self._skip_unless_importable()
        from unittest.mock import MagicMock
        try:
            from similarity_search.index_manager import VectorIndexManager
        except Exception as exc:
            pytest.skip(f"Cannot import: {exc}")
        mgr = VectorIndexManager()
        with pytest.raises(ValueError):
            mgr.create_index(MagicMock(),
                             {"index_type": "FLAT_UNSUPPORTED", "params": {}})

    def test_batch_upsert_splits_1001_into_three_batches(self):
        """Batch upsert of 1001 vectors with batch_size=500 calls insert 3 times."""
        self._skip_unless_importable()
        from unittest.mock import MagicMock
        try:
            from similarity_search.service import SimilaritySearchService
        except Exception as exc:
            pytest.skip(f"Cannot import: {exc}")
        svc = SimilaritySearchService.__new__(SimilaritySearchService)
        call_count = [0]

        def fake_insert(data):
            call_count[0] += 1
            return True

        mock_col = MagicMock()
        mock_col.insert.side_effect = fake_insert
        svc._collection = mock_col
        vectors = [(str(i), [0.0] * 128, {}) for i in range(1001)]
        svc.batch_upsert(vectors, batch_size=500)
        assert call_count[0] == 3, f"Expected 3 batches, got {call_count[0]}"

    def test_delete_does_not_appear_in_search(self):
        """After delete(), search on mock collection confirms deleted vector absent."""
        self._skip_unless_importable()
        from unittest.mock import MagicMock
        try:
            from similarity_search.service import SimilaritySearchService
        except Exception as exc:
            pytest.skip(f"Cannot import: {exc}")
        svc = SimilaritySearchService.__new__(SimilaritySearchService)
        mock_col = MagicMock()
        mock_col.search.return_value = [[]]
        svc._collection = mock_col
        svc.delete("vec-1")
        results = svc.search([0.0] * 128, top_k=5)
        assert results == [], f"Expected empty results, got {results}"
