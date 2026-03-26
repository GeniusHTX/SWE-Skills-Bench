"""
Test for 'rag-implementation' skill — RAG Implementation Framework
Validates that the Agent created an end-to-end RAG demo for LangChain
with document loading, vector indexing, semantic retrieval, and generation.
"""

import os
import re
import subprocess

import pytest

from _dependency_utils import ensure_python_dependencies


@pytest.fixture(scope="module", autouse=True)
def _ensure_repo_dependencies():
    ensure_python_dependencies(TestRagImplementation.REPO_DIR)


class TestRagImplementation:
    """Verify RAG demonstration script for LangChain."""

    REPO_DIR = "/workspace/langchain"

    def _read(self, *parts):
        fpath = os.path.join(self.REPO_DIR, *parts)
        assert os.path.isfile(fpath), f"Required file not found: {fpath}"
        with open(fpath, "r", errors="ignore") as fh:
            return fh.read()

    # ------------------------------------------------------------------
    # L1: File existence and syntax
    # ------------------------------------------------------------------

    def test_demo_file_exists(self):
        """examples/rag_demo.py must exist."""
        assert os.path.isfile(os.path.join(self.REPO_DIR, "examples", "rag_demo.py"))

    def test_demo_compiles(self):
        """rag_demo.py must be syntactically valid Python."""
        result = subprocess.run(
            ["python", "-m", "py_compile", "examples/rag_demo.py"],
            cwd=self.REPO_DIR,
            capture_output=True,
            text=True,
            timeout=30,
        )
        assert result.returncode == 0, f"Syntax error:\n{result.stderr}"

    def test_has_main_entry_point(self):
        """Script must have a __main__ entry point."""
        content = self._read("examples", "rag_demo.py")
        assert re.search(r'if\s+__name__\s*==\s*["\']__main__["\']', content)

    # ------------------------------------------------------------------
    # L1: Document loading and chunking
    # ------------------------------------------------------------------

    def test_loads_documents(self):
        """Script must load documents from a source."""
        content = self._read("examples", "rag_demo.py")
        patterns = [
            r"load",
            r"Loader",
            r"read",
            r"open\(",
            r"documents",
            r"TextLoader",
            r"DirectoryLoader",
            r"sample.*data",
        ]
        assert any(
            re.search(p, content, re.IGNORECASE) for p in patterns
        ), "Script does not load documents"

    def test_splits_documents_into_chunks(self):
        """Script must split documents into chunks."""
        content = self._read("examples", "rag_demo.py")
        patterns = [
            r"split",
            r"chunk",
            r"TextSplitter",
            r"RecursiveCharacterTextSplitter",
            r"CharacterTextSplitter",
        ]
        assert any(
            re.search(p, content, re.IGNORECASE) for p in patterns
        ), "Script does not split documents into chunks"

    def test_chunk_size_configurable(self):
        """Chunk size must be configurable."""
        content = self._read("examples", "rag_demo.py")
        patterns = [r"chunk_size", r"chunk_overlap", r"max_length"]
        assert any(
            re.search(p, content) for p in patterns
        ), "Chunk size is not configurable"

    # ------------------------------------------------------------------
    # L1: Vector store
    # ------------------------------------------------------------------

    def test_creates_vector_store(self):
        """Script must create a vector store from document chunks."""
        content = self._read("examples", "rag_demo.py")
        patterns = [
            r"vector.*store",
            r"VectorStore",
            r"FAISS",
            r"Chroma",
            r"embedding",
            r"Embedding",
            r"from_documents",
            r"from_texts",
        ]
        assert any(
            re.search(p, content, re.IGNORECASE) for p in patterns
        ), "Script does not create a vector store"

    def test_uses_embeddings(self):
        """Script must use an embedding model/function."""
        content = self._read("examples", "rag_demo.py")
        patterns = [
            r"[Ee]mbedding",
            r"embed",
            r"OpenAIEmbeddings",
            r"HuggingFaceEmbeddings",
            r"SentenceTransformer",
        ]
        assert any(
            re.search(p, content) for p in patterns
        ), "Script does not use embeddings"

    # ------------------------------------------------------------------
    # L1: Retrieval and generation
    # ------------------------------------------------------------------

    def test_performs_similarity_search(self):
        """Script must perform similarity search against the vector store."""
        content = self._read("examples", "rag_demo.py")
        patterns = [
            r"similarity_search",
            r"search",
            r"retrieve",
            r"retriever",
            r"as_retriever",
            r"top_k",
            r"k=",
        ]
        assert any(
            re.search(p, content) for p in patterns
        ), "Script does not perform similarity search"

    def test_configurable_top_k(self):
        """Top-k retrieval must be configurable."""
        content = self._read("examples", "rag_demo.py")
        patterns = [
            r"top_k",
            r"k\s*=",
            r"search_kwargs.*k",
            r"num_results",
            r"n_results",
        ]
        assert any(re.search(p, content) for p in patterns), "Top-k is not configurable"

    def test_constructs_prompt_with_context(self):
        """Script must construct a prompt that includes retrieved context."""
        content = self._read("examples", "rag_demo.py")
        patterns = [
            r"context",
            r"prompt.*template|template.*prompt",
            r"RetrievalQA",
            r"stuff",
            r"map_reduce",
            r"retrieved.*document|document.*retrieved",
        ]
        assert any(
            re.search(p, content, re.IGNORECASE) for p in patterns
        ), "Script does not construct a prompt with retrieved context"

    def test_generates_answer(self):
        """Script must generate an answer using an LLM interface."""
        content = self._read("examples", "rag_demo.py")
        patterns = [
            r"llm",
            r"LLM",
            r"ChatOpenAI",
            r"generate",
            r"invoke",
            r"predict",
            r"run",
            r"chain",
        ]
        assert any(
            re.search(p, content) for p in patterns
        ), "Script does not generate an answer"

    def test_returns_source_references(self):
        """Output must include source references pointing to retrieved chunks."""
        content = self._read("examples", "rag_demo.py")
        patterns = [
            r"source",
            r"reference",
            r"metadata",
            r"page_content",
            r"source_documents",
        ]
        assert any(
            re.search(p, content, re.IGNORECASE) for p in patterns
        ), "Script does not return source references"

    # ------------------------------------------------------------------
    # L2: Configuration
    # ------------------------------------------------------------------

    def test_model_parameters_configurable(self):
        """Model parameters (temperature, max_tokens) must be configurable."""
        content = self._read("examples", "rag_demo.py")
        patterns = [r"temperature", r"max_tokens", r"model_name"]
        assert any(
            re.search(p, content) for p in patterns
        ), "Model parameters not configurable"
