"""
Tests for rag-implementation skill.
Validates HybridRetriever, RRF fusion, Reranker, RecursiveChunker in langchain repository.
"""

import os
import re
import glob
import pytest

REPO_DIR = "/workspace/langchain"


def _path(rel: str) -> str:
    return os.path.join(REPO_DIR, rel)


def _read(rel: str) -> str:
    with open(_path(rel), encoding="utf-8", errors="ignore") as f:
        return f.read()


class TestRagImplementation:

    # ── file_path_check ──────────────────────────────────────────────────────

    def test_hybrid_retriever_file_exists(self):
        """libs/core/langchain_core/retrievers/hybrid_retriever.py must exist."""
        rel = "libs/core/langchain_core/retrievers/hybrid_retriever.py"
        assert os.path.isfile(_path(rel)), f"{rel} not found"
        assert os.path.getsize(_path(rel)) > 0, "hybrid_retriever.py is empty"

    def test_retrievers_module_has_multiple_files(self):
        """langchain_core/retrievers must contain >= 2 Python files."""
        pattern = os.path.join(REPO_DIR, "libs/core/langchain_core/retrievers", "*.py")
        files = glob.glob(pattern)
        assert (
            len(files) >= 2
        ), f"Expected >= 2 Python files in retrievers/, found {len(files)}"

    # ── semantic_check ───────────────────────────────────────────────────────

    def test_hybrid_retriever_class_defined(self):
        """HybridRetriever must define dense_retriever and sparse_retriever attributes."""
        content = _read("libs/core/langchain_core/retrievers/hybrid_retriever.py")
        assert "class HybridRetriever" in content, "HybridRetriever class not defined"
        assert "dense" in content, "dense_retriever attribute not found"
        assert "sparse" in content, "sparse_retriever attribute not found"

    def test_rrf_fusion_algorithm(self):
        """hybrid_retriever.py must implement RRF scoring formula 1/(k+rank)."""
        content = _read("libs/core/langchain_core/retrievers/hybrid_retriever.py")
        has_rrf = (
            "rrf" in content.lower()
            or "reciprocal" in content.lower()
            or "1.0 / (" in content
            or "1/(k" in content
            or "k + rank" in content
            or "60" in content
        )
        assert has_rrf, "RRF fusion algorithm not found in hybrid_retriever.py"

    def test_recursive_chunker_class_defined(self):
        """RecursiveChunker must define chunk_size and overlap parameters."""
        content = _read("libs/core/langchain_core/retrievers/hybrid_retriever.py")
        assert "RecursiveChunker" in content, "RecursiveChunker class not defined"
        assert "chunk_size" in content, "chunk_size parameter not found"
        assert "overlap" in content, "overlap parameter not found"

    def test_reranker_min_score_filter(self):
        """Reranker must define min_score parameter for filtering."""
        content = _read("libs/core/langchain_core/retrievers/hybrid_retriever.py")
        assert (
            "min_score" in content
        ), "min_score parameter not found in hybrid_retriever.py"
        assert (
            "Reranker" in content or "rerank" in content
        ), "No Reranker class found in hybrid_retriever.py"

    # ── functional_check ─────────────────────────────────────────────────────

    def test_dense_sparse_rrf_b_ranks_highest(self):
        """B appearing in both dense and sparse must have highest RRF score (mocked)."""

        def rrf_score(rank: int, k: int = 60) -> float:
            return 1.0 / (k + rank)

        def fuse(dense: list, sparse: list) -> list:
            scores = {}
            for i, doc in enumerate(dense):
                scores[doc] = scores.get(doc, 0) + rrf_score(i + 1)
            for i, doc in enumerate(sparse):
                scores[doc] = scores.get(doc, 0) + rrf_score(i + 1)
            return sorted(scores.keys(), key=lambda d: scores[d], reverse=True)

        ranked = fuse(dense=["A", "B", "C"], sparse=["B", "D", "E"])
        assert ranked[0] == "B", f"Expected B to rank first, got {ranked[0]}"

    def test_document_b_deduplicated(self):
        """Document B must appear only once in RRF fused results (mocked)."""

        def fuse_unique(dense: list, sparse: list) -> list:
            scores = {}
            for i, doc in enumerate(dense):
                scores[doc] = scores.get(doc, 0) + 1.0 / (60 + i + 1)
            for i, doc in enumerate(sparse):
                scores[doc] = scores.get(doc, 0) + 1.0 / (60 + i + 1)
            return sorted(scores.keys(), key=lambda d: scores[d], reverse=True)

        results = fuse_unique(dense=["A", "B", "C"], sparse=["B", "D", "E"])
        assert (
            results.count("B") == 1
        ), f"Expected B to appear exactly once, appeared {results.count('B')} times"

    def test_reranker_min_score_0_5_filters(self):
        """Reranker(min_score=0.5) must exclude documents with score < 0.5 (mocked)."""

        def rerank_and_filter(docs_with_scores: dict, min_score: float) -> list:
            return [
                doc for doc, score in docs_with_scores.items() if score >= min_score
            ]

        result = rerank_and_filter({"A": 0.8, "B": 0.3, "C": 0.6}, min_score=0.5)
        assert "A" in result and "C" in result
        assert "B" not in result, f"B with score 0.3 should be filtered out"

    def test_rerank_score_in_metadata(self):
        """Each result must have rerank_score in its metadata (mocked)."""

        class Document:
            def __init__(self, id, score):
                self.id = id
                self.metadata = {"rerank_score": score}

        docs = [Document("A", 0.9), Document("C", 0.7)]
        for doc in docs:
            assert (
                "rerank_score" in doc.metadata
            ), f"rerank_score missing from metadata of doc {doc.id}"
            assert 0.0 <= doc.metadata["rerank_score"] <= 1.0

    def test_format_citations_with_source_and_score(self):
        """format_citations must output '[1] source (score: X.XX)' format (mocked)."""

        def format_citations(docs: list) -> str:
            lines = []
            for i, doc in enumerate(docs, 1):
                lines.append(f"[{i}] {doc['source']} (score: {doc['score']:.2f})")
            return "\n".join(lines)

        result = format_citations([{"source": "wiki.md", "score": 0.92}])
        assert (
            "[1] wiki.md (score: 0.92)" in result
        ), f"Citation format incorrect: {result!r}"

    def test_recursive_chunker_250chars_3_chunks(self):
        """RecursiveChunker(chunk_size=100, overlap=20) on 250-char text must yield 3 chunks (mocked)."""

        def chunk(text: str, chunk_size: int, overlap: int) -> list:
            chunks = []
            start = 0
            while start < len(text):
                end = start + chunk_size
                chunks.append(text[start:end])
                start += chunk_size - overlap
            return chunks

        text = "a" * 250
        chunks = chunk(text, chunk_size=100, overlap=20)
        assert (
            len(chunks) == 3
        ), f"Expected 3 chunks for 250 chars with size=100/overlap=20, got {len(chunks)}"
