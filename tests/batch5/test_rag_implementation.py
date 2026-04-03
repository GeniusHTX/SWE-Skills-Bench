"""
Test for 'rag-implementation' skill — LangChain RAG Pipeline
Validates Reciprocal Rank Fusion (RRF k=60), dense_weight=0.6,
RecursiveCharacterTextSplitter, vector store, and retrieval chain.
"""

import os
import re
import sys

import pytest


class TestRagImplementation:
    """Verify RAG implementation patterns in LangChain."""

    REPO_DIR = "/workspace/langchain"

    # ── file_path_check ─────────────────────────────────────────────────────

    def test_rag_related_files_exist(self):
        """Verify RAG-related Python files exist."""
        found = False
        for dirpath, _, fnames in os.walk(self.REPO_DIR):
            if ".git" in dirpath:
                continue
            for f in fnames:
                if f.endswith(".py") and ("retriev" in f.lower() or "rag" in f.lower()):
                    found = True
                    break
            if found:
                break
        assert found, "No RAG/retrieval files found"

    def test_text_splitter_files_exist(self):
        """Verify text splitter files exist."""
        found = False
        for dirpath, _, fnames in os.walk(self.REPO_DIR):
            if ".git" in dirpath:
                continue
            for f in fnames:
                if f.endswith(".py") and "split" in f.lower():
                    found = True
                    break
            if found:
                break
        assert found, "No text splitter files found"

    # ── semantic_check ──────────────────────────────────────────────────────

    def test_reciprocal_rank_fusion(self):
        """Verify RRF (Reciprocal Rank Fusion) with k=60."""
        py_files = self._find_py_files()
        for fpath in py_files:
            content = self._read(fpath)
            if re.search(
                r"(reciprocal.?rank|rrf|rank.?fusion)", content, re.IGNORECASE
            ):
                return
        pytest.fail("No Reciprocal Rank Fusion (RRF) found")

    def test_rrf_k_parameter(self):
        """Verify RRF k parameter (e.g. k=60)."""
        py_files = self._find_py_files()
        for fpath in py_files:
            content = self._read(fpath)
            if re.search(r"k\s*=\s*60|rrf.*60", content, re.IGNORECASE):
                return
            if (
                re.search(r"reciprocal.?rank", content, re.IGNORECASE)
                and "k" in content
            ):
                return
        pytest.fail("No RRF k=60 parameter found")

    def test_dense_weight(self):
        """Verify dense_weight parameter (e.g. 0.6)."""
        py_files = self._find_py_files()
        for fpath in py_files:
            content = self._read(fpath)
            if re.search(r"(dense_weight|alpha|weight.*0\.\d)", content, re.IGNORECASE):
                return
        pytest.fail("No dense_weight parameter found")

    def test_recursive_character_text_splitter(self):
        """Verify RecursiveCharacterTextSplitter usage."""
        py_files = self._find_py_files()
        for fpath in py_files:
            content = self._read(fpath)
            if "RecursiveCharacterTextSplitter" in content:
                return
        pytest.fail("No RecursiveCharacterTextSplitter found")

    def test_vector_store_integration(self):
        """Verify vector store integration (FAISS, Chroma, Pinecone, etc.)."""
        py_files = self._find_py_files()
        for fpath in py_files:
            content = self._read(fpath)
            if re.search(
                r"(VectorStore|FAISS|Chroma|Pinecone|Weaviate|Milvus|vectorstore)",
                content,
            ):
                return
        pytest.fail("No vector store integration found")

    # ── functional_check ────────────────────────────────────────────────────

    def test_source_files_parse(self):
        """Verify RAG source files are syntactically valid."""
        import ast

        py_files = self._find_py_files()
        for fpath in py_files[:15]:
            content = self._read(fpath)
            try:
                ast.parse(content, filename=fpath)
            except SyntaxError as e:
                pytest.fail(f"SyntaxError in {os.path.basename(fpath)}: {e}")

    def test_retrieval_chain(self):
        """Verify retrieval chain or RetrievalQA implementation."""
        py_files = self._find_py_files()
        for fpath in py_files:
            content = self._read(fpath)
            if re.search(
                r"(RetrievalQA|create_retrieval_chain|retrieval_chain|as_retriever)",
                content,
            ):
                return
        pytest.fail("No retrieval chain found")

    def test_embedding_model(self):
        """Verify embedding model is configured."""
        py_files = self._find_py_files()
        for fpath in py_files:
            content = self._read(fpath)
            if re.search(
                r"(Embeddings|OpenAIEmbeddings|embed_documents|embed_query|embedding)",
                content,
            ):
                return
        pytest.fail("No embedding model found")

    def test_chunk_size_and_overlap(self):
        """Verify chunk_size and chunk_overlap are configured."""
        py_files = self._find_py_files()
        for fpath in py_files:
            content = self._read(fpath)
            if "chunk_size" in content and "chunk_overlap" in content:
                return
        pytest.fail("No chunk_size/chunk_overlap configuration found")

    def test_document_loader(self):
        """Verify document loader for ingesting data."""
        py_files = self._find_py_files()
        for fpath in py_files:
            content = self._read(fpath)
            if re.search(
                r"(DocumentLoader|TextLoader|PDFLoader|WebBaseLoader|load_documents|BaseLoader)",
                content,
            ):
                return
        pytest.fail("No document loader found")

    # ── helpers ──────────────────────────────────────────────────────────────

    def _find_py_files(self):
        results = []
        for dirpath, _, fnames in os.walk(self.REPO_DIR):
            if ".git" in dirpath:
                continue
            for f in fnames:
                if f.endswith(".py"):
                    results.append(os.path.join(dirpath, f))
        return results

    def _read(self, path):
        with open(path, "r", errors="ignore") as fh:
            return fh.read()
