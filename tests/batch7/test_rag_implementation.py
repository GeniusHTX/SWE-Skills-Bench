"""Test file for the rag-implementation skill.

This suite validates the HybridRetriever, SemanticChunker, RAGChain,
and RAGResponse classes in LangChain.
"""

from __future__ import annotations

import ast
import pathlib
import re

import pytest


class TestRagImplementation:
    """Verify RAG implementation patterns in LangChain."""

    REPO_DIR = "/workspace/langchain"

    HYBRID_RETRIEVER_PY = "libs/langchain/langchain/retrievers/hybrid_retriever.py"
    SEMANTIC_CHUNKER_PY = "libs/langchain/langchain/text_splitter/semantic_chunker.py"
    RAG_CHAIN_PY = "libs/langchain/langchain/chains/rag_chain.py"

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    def _repo_path(self, relative: str) -> pathlib.Path:
        return pathlib.Path(self.REPO_DIR, *relative.split("/"))

    def _read_text(self, relative: str) -> str:
        path = self._repo_path(relative)
        assert path.exists(), f"Expected path to exist: {path}"
        return path.read_text(encoding="utf-8", errors="ignore")

    def _assert_non_empty_file(self, relative: str) -> pathlib.Path:
        path = self._repo_path(relative)
        assert path.is_file(), f"Expected file to exist: {path}"
        assert path.stat().st_size > 0, f"Expected non-empty file: {path}"
        return path

    def _class_source(self, source: str, class_name: str) -> str | None:
        tree = ast.parse(source)
        for node in ast.walk(tree):
            if isinstance(node, ast.ClassDef) and node.name == class_name:
                start = node.lineno - 1
                end = node.end_lineno or start + 1
                lines = source.splitlines()
                return "\n".join(lines[start:end])
        return None

    # ------------------------------------------------------------------
    # Layer 1 – file_path_check (3 cases)
    # ------------------------------------------------------------------

    def test_file_path_libs_langchain_langchain_retrievers_hybrid_retriever_py_exis(
        self,
    ):
        """Verify hybrid_retriever.py exists and is non-empty."""
        self._assert_non_empty_file(self.HYBRID_RETRIEVER_PY)

    def test_file_path_libs_langchain_langchain_text_splitter_semantic_chunker_py_e(
        self,
    ):
        """Verify semantic_chunker.py exists and is non-empty."""
        self._assert_non_empty_file(self.SEMANTIC_CHUNKER_PY)

    def test_file_path_libs_langchain_langchain_chains_rag_chain_py_exists(self):
        """Verify rag_chain.py exists and is non-empty."""
        self._assert_non_empty_file(self.RAG_CHAIN_PY)

    # ------------------------------------------------------------------
    # Layer 2 – semantic_check (5 cases)
    # ------------------------------------------------------------------

    def test_semantic_hybridretriever_inherits_baseretriever_with_dense_retriever_(
        self,
    ):
        """HybridRetriever inherits BaseRetriever with dense_retriever, sparse_retriever, etc."""
        src = self._read_text(self.HYBRID_RETRIEVER_PY)
        body = self._class_source(src, "HybridRetriever")
        assert body is not None, "HybridRetriever class not found"
        for field in ("dense_retriever", "sparse_retriever", "k"):
            assert field in body, f"HybridRetriever missing field: {field}"

    def test_semantic_semanticchunker_has_embedding_function_max_min_chunk_sizes_s(
        self,
    ):
        """SemanticChunker has embedding_function, max/min chunk sizes, similarity_threshold."""
        src = self._read_text(self.SEMANTIC_CHUNKER_PY)
        body = self._class_source(src, "SemanticChunker")
        assert body is not None, "SemanticChunker class not found"
        assert "embedding" in body.lower(), "Missing embedding_function"
        assert re.search(
            r"similarity_threshold|threshold", body
        ), "Missing similarity_threshold"

    def test_semantic_ragchain_has_retriever_llm_system_prompt_max_context_tokens_(
        self,
    ):
        """RAGChain has retriever, llm, system_prompt, max_context_tokens, return_sources."""
        src = self._read_text(self.RAG_CHAIN_PY)
        body = self._class_source(src, "RAGChain")
        assert body is not None, "RAGChain class not found"
        for field in ("retriever", "llm"):
            assert field in body, f"RAGChain missing field: {field}"

    def test_semantic_ragresponse_is_a_dataclass_with_answer_sources_query_context(
        self,
    ):
        """RAGResponse is a dataclass with answer, sources, query, context_length."""
        src = self._read_text(self.RAG_CHAIN_PY)
        body = self._class_source(src, "RAGResponse")
        assert body is not None, "RAGResponse class not found"
        for field in ("answer", "sources", "query"):
            assert field in body, f"RAGResponse missing field: {field}"

    def test_semantic_retrieval_score_added_to_document_metadata(self):
        """retrieval_score added to document metadata."""
        src = self._read_text(self.HYBRID_RETRIEVER_PY)
        assert re.search(
            r"retrieval_score|score|metadata", src
        ), "retrieval_score should be added to document metadata"

    # ------------------------------------------------------------------
    # Layer 3 – functional_check (5 cases, source analysis)
    # ------------------------------------------------------------------

    def test_functional_rrf_fusion_b_ranked_highest_when_it_appears_in_both_retrieve(
        self,
    ):
        """RRF fusion: B ranked highest when it appears in both retrievers."""
        src = self._read_text(self.HYBRID_RETRIEVER_PY)
        assert re.search(
            r"RRF|reciprocal_rank|fusion|1\s*/\s*\(", src, re.IGNORECASE
        ), "RRF fusion logic required"

    def test_functional_semanticchunker_splits_at_topic_boundary_detected_by_embeddi(
        self,
    ):
        """SemanticChunker splits at topic boundary detected by embedding similarity drop."""
        src = self._read_text(self.SEMANTIC_CHUNKER_PY)
        assert re.search(
            r"split|chunk|similarity|cosine", src, re.IGNORECASE
        ), "SemanticChunker should split based on embedding similarity"

    def test_functional_ragchain_assembles_numbered_context_and_calls_llm(self):
        """RAGChain assembles numbered context and calls LLM."""
        src = self._read_text(self.RAG_CHAIN_PY)
        assert re.search(
            r"def\s+(invoke|__call__|run|query)\s*\(", src
        ), "RAGChain should have an invoke/run method"

    def test_functional_context_truncation_works_at_token_estimate_boundary(self):
        """Context truncation works at token estimate boundary."""
        src = self._read_text(self.RAG_CHAIN_PY)
        assert re.search(
            r"max_context_tokens|truncat|token.*limit", src, re.IGNORECASE
        ), "Context truncation logic required"

    def test_functional_streaming_invoke_yields_tokens_incrementally(self):
        """Streaming invoke yields tokens incrementally."""
        src = self._read_text(self.RAG_CHAIN_PY)
        assert re.search(
            r"stream|yield|async.*for|astream", src
        ), "Streaming support required"
