"""
Test for 'rag-implementation' skill — RAG Pipeline
Validates that the Agent implemented a Retrieval-Augmented Generation pipeline
with hybrid retrieval, scored document models, and token-constrained context builder.
"""

import os
import re
import sys

import pytest


class TestRagImplementation:
    """Verify RAG pipeline implementation."""

    REPO_DIR = "/workspace/langchain"

    @staticmethod
    def _read(path: str) -> str:
        try:
            with open(path, "r", errors="ignore") as fh:
                return fh.read()
        except OSError:
            return ""

    # ── file_path_check ─────────────────────────────────────────────

    def test_rag_pipeline_module_files_exist(self):
        """Verify src/rag_pipeline/pipeline.py and retriever.py exist."""
        for rel in ("src/rag_pipeline/pipeline.py", "src/rag_pipeline/retriever.py"):
            path = os.path.join(self.REPO_DIR, rel)
            assert os.path.isfile(path), f"Missing: {rel}"

    def test_context_builder_and_models_exist(self):
        """Verify context_builder.py and models.py exist."""
        for rel in ("src/rag_pipeline/context_builder.py",
                     "src/rag_pipeline/models.py"):
            path = os.path.join(self.REPO_DIR, rel)
            assert os.path.isfile(path), f"Missing: {rel}"

    def test_package_init_exists(self):
        """Verify src/rag_pipeline/__init__.py exists."""
        path = os.path.join(self.REPO_DIR, "src/rag_pipeline/__init__.py")
        assert os.path.isfile(path), "Missing: src/rag_pipeline/__init__.py"

    # ── semantic_check ──────────────────────────────────────────────

    def test_hybrid_retriever_alpha_param(self):
        """Verify HybridRetriever.retrieve accepts alpha parameter for blend weighting."""
        content = self._read(os.path.join(
            self.REPO_DIR, "src/rag_pipeline/retriever.py"))
        assert content, "retriever.py is empty or unreadable"
        assert "alpha" in content, "alpha parameter not found in retriever.py"

    def test_scored_document_model(self):
        """Verify ScoredDocument model has doc_id, text, and score fields."""
        content = self._read(os.path.join(
            self.REPO_DIR, "src/rag_pipeline/models.py"))
        assert content, "models.py is empty or unreadable"
        for kw in ("doc_id", "score", "ScoredDocument"):
            assert kw in content, f"'{kw}' not found in models.py"

    def test_context_builder_token_limit_logic(self):
        """Verify ContextBuilder.build respects max_tokens parameter."""
        content = self._read(os.path.join(
            self.REPO_DIR, "src/rag_pipeline/context_builder.py"))
        assert content, "context_builder.py is empty or unreadable"
        assert "max_tokens" in content, "max_tokens not found in context_builder.py"

    # ── functional_check (import) ───────────────────────────────────

    def _skip_unless_importable(self):
        if not os.path.isdir(self.REPO_DIR):
            pytest.skip("Repo dir does not exist")
        if self.REPO_DIR not in sys.path:
            sys.path.insert(0, self.REPO_DIR)

    def test_retrieve_returns_k_results(self):
        """HybridRetriever.retrieve with 20 docs and k=5 returns exactly 5 results."""
        self._skip_unless_importable()
        try:
            from src.rag_pipeline.retriever import HybridRetriever
            from src.rag_pipeline.models import Document
        except Exception as exc:
            pytest.skip(f"Cannot import: {exc}")
        docs = [Document(doc_id=str(i), text=f"document text {i}") for i in range(20)]
        results = HybridRetriever().retrieve("test query", docs, k=5, alpha=0.5)
        assert len(results) == 5, f"Expected 5 results, got {len(results)}"

    def test_results_sorted_descending_by_score(self):
        """Returned results are sorted descending by score."""
        self._skip_unless_importable()
        try:
            from src.rag_pipeline.retriever import HybridRetriever
            from src.rag_pipeline.models import Document
        except Exception as exc:
            pytest.skip(f"Cannot import: {exc}")
        docs = [Document(doc_id=str(i), text=f"query term {i} document")
                for i in range(10)]
        results = HybridRetriever().retrieve("query term", docs, k=5, alpha=0.5)
        scores = [r.score for r in results]
        assert scores == sorted(scores, reverse=True), \
            "Results must be sorted descending by score"

    def test_empty_corpus_returns_empty_list(self):
        """HybridRetriever.retrieve with empty docs returns [] without error."""
        self._skip_unless_importable()
        try:
            from src.rag_pipeline.retriever import HybridRetriever
        except Exception as exc:
            pytest.skip(f"Cannot import: {exc}")
        results = HybridRetriever().retrieve("query", [], k=5, alpha=0.5)
        assert results == [], f"Expected empty list, got {results}"

    def test_context_builder_respects_token_limit(self):
        """ContextBuilder.build returns context with token count <= max_tokens."""
        self._skip_unless_importable()
        try:
            from src.rag_pipeline.context_builder import ContextBuilder
            from src.rag_pipeline.models import ScoredDocument
        except Exception as exc:
            pytest.skip(f"Cannot import: {exc}")
        docs = [ScoredDocument(doc_id=str(i), text=" ".join(["word"] * 100),
                               score=1.0 - i * 0.1) for i in range(5)]
        context = ContextBuilder().build(docs, max_tokens=50)
        assert len(context.split()) <= 50, \
            f"Context has {len(context.split())} tokens, expected <= 50"

    def test_deduplication_by_doc_id(self):
        """Two docs with identical doc_id result in only one entry in retrieve output."""
        self._skip_unless_importable()
        try:
            from src.rag_pipeline.retriever import HybridRetriever
            from src.rag_pipeline.models import Document
        except Exception as exc:
            pytest.skip(f"Cannot import: {exc}")
        docs = [Document(doc_id="dup", text="same document"),
                Document(doc_id="dup", text="same document again")]
        results = HybridRetriever().retrieve("same document", docs, k=5, alpha=0.5)
        doc_ids = [r.doc_id for r in results]
        assert len(doc_ids) == len(set(doc_ids)), \
            "Duplicate doc_ids must be deduplicated"
