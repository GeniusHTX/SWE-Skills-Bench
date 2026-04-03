"""
Test for 'rag-implementation' skill — RAG Implementation
Validates HybridRetriever with BM25 + embedding-based retrieval, alpha blending, and document management.
"""

import os
import re
import sys
import glob
import pytest


class TestRagImplementation:
    """Tests for RAG implementation with HybridRetriever in langchain repo."""

    REPO_DIR = "/workspace/langchain"

    def _read(self, relpath):
        full = os.path.join(self.REPO_DIR, relpath)
        with open(full, "r", errors="ignore") as f:
            return f.read()

    # --- File Path Checks ---

    def test_hybrid_retriever_py_exists(self):
        """Verifies that the HybridRetriever implementation file exists."""
        pattern = os.path.join(self.REPO_DIR, "**", "hybrid_retriever.py")
        matches = glob.glob(pattern, recursive=True)
        assert len(matches) > 0, "hybrid_retriever.py not found anywhere in the repo"

    def test_hybrid_retriever_init_exists(self):
        """Verifies that the __init__.py exists alongside the retriever module."""
        pattern = os.path.join(self.REPO_DIR, "**", "hybrid_retriever.py")
        matches = glob.glob(pattern, recursive=True)
        assert len(matches) > 0, "hybrid_retriever.py not found"
        parent = os.path.dirname(matches[0])
        init_file = os.path.join(parent, "__init__.py")
        assert os.path.exists(init_file), f"__init__.py not found in {parent}"

    # --- Semantic Checks ---

    def test_sem_class_hybrid_retriever_defined(self):
        """HybridRetriever class is defined in the source."""
        pattern = os.path.join(self.REPO_DIR, "**", "hybrid_retriever.py")
        matches = glob.glob(pattern, recursive=True)
        assert len(matches) > 0, "hybrid_retriever.py not found"
        content = self._read(os.path.relpath(matches[0], self.REPO_DIR))
        assert re.search(
            r"class\s+HybridRetriever", content
        ), "class HybridRetriever not found"

    def test_sem_constructor_has_embedding_function_documents_alpha(self):
        """HybridRetriever constructor has embedding_function, documents, and alpha=0.5 parameters."""
        pattern = os.path.join(self.REPO_DIR, "**", "hybrid_retriever.py")
        matches = glob.glob(pattern, recursive=True)
        assert len(matches) > 0
        content = self._read(os.path.relpath(matches[0], self.REPO_DIR))
        assert "embedding_function" in content, "embedding_function parameter not found"
        assert "documents" in content, "documents parameter not found"
        assert re.search(r"alpha\s*=\s*0\.5", content), "alpha=0.5 default not found"

    def test_sem_methods_exist(self):
        """HybridRetriever has add_documents, retrieve, retrieve_with_scores, get_document_count methods."""
        pattern = os.path.join(self.REPO_DIR, "**", "hybrid_retriever.py")
        matches = glob.glob(pattern, recursive=True)
        assert len(matches) > 0
        content = self._read(os.path.relpath(matches[0], self.REPO_DIR))
        for method in [
            "add_documents",
            "retrieve",
            "retrieve_with_scores",
            "get_document_count",
        ]:
            assert re.search(
                rf"def\s+{method}\s*\(", content
            ), f"Method {method} not found"

    # --- Functional Checks (import) ---

    def _find_and_add_module(self):
        """Helper to find hybrid_retriever.py and add its parent to sys.path."""
        pattern = os.path.join(self.REPO_DIR, "**", "hybrid_retriever.py")
        matches = glob.glob(pattern, recursive=True)
        assert len(matches) > 0, "hybrid_retriever.py not found"
        module_dir = os.path.dirname(matches[0])
        parent_dir = os.path.dirname(module_dir)
        pkg_name = os.path.basename(module_dir)
        return parent_dir, pkg_name

    def test_func_import_hybrid_retriever(self):
        """from <package>.hybrid_retriever import HybridRetriever — importable."""
        parent_dir, pkg_name = self._find_and_add_module()
        old_path = sys.path[:]
        sys.path.insert(0, parent_dir)
        try:
            mod = __import__(
                f"{pkg_name}.hybrid_retriever", fromlist=["HybridRetriever"]
            )
            HybridRetriever = getattr(mod, "HybridRetriever")
            assert HybridRetriever is not None
        finally:
            sys.path[:] = old_path

    def test_func_retrieve_returns_relevant_doc_first(self):
        """retrieve('python') returns 'python programming guide' as the first result."""
        parent_dir, pkg_name = self._find_and_add_module()
        old_path = sys.path[:]
        sys.path.insert(0, parent_dir)
        try:
            mod = __import__(
                f"{pkg_name}.hybrid_retriever", fromlist=["HybridRetriever"]
            )
            HybridRetriever = getattr(mod, "HybridRetriever")
            docs = ["python programming guide", "java basics", "cooking recipes"]
            retriever = HybridRetriever(
                embedding_function=lambda texts: [[1.0] * 32 for _ in texts],
                documents=docs,
                alpha=0.5,
            )
            results = retriever.retrieve("python")
            assert len(results) > 0, "retrieve returned empty"
            assert (
                "python" in results[0].lower()
            ), f"First result should be python-related, got: {results[0]}"
        finally:
            sys.path[:] = old_path

    def test_func_retrieve_k_limits_results(self):
        """retrieve with k=1 returns only 1 result."""
        parent_dir, pkg_name = self._find_and_add_module()
        old_path = sys.path[:]
        sys.path.insert(0, parent_dir)
        try:
            mod = __import__(
                f"{pkg_name}.hybrid_retriever", fromlist=["HybridRetriever"]
            )
            HybridRetriever = getattr(mod, "HybridRetriever")
            docs = ["python programming guide", "java basics", "cooking recipes"]
            retriever = HybridRetriever(
                embedding_function=lambda texts: [[1.0] * 32 for _ in texts],
                documents=docs,
                alpha=0.5,
            )
            results = retriever.retrieve("python", k=1)
            assert len(results) == 1, f"Expected 1 result but got {len(results)}"
        finally:
            sys.path[:] = old_path

    def test_func_retrieve_k_greater_than_num_docs_returns_all(self):
        """retrieve with k>num_docs returns all documents."""
        parent_dir, pkg_name = self._find_and_add_module()
        old_path = sys.path[:]
        sys.path.insert(0, parent_dir)
        try:
            mod = __import__(
                f"{pkg_name}.hybrid_retriever", fromlist=["HybridRetriever"]
            )
            HybridRetriever = getattr(mod, "HybridRetriever")
            docs = ["python programming guide", "java basics", "cooking recipes"]
            retriever = HybridRetriever(
                embedding_function=lambda texts: [[1.0] * 32 for _ in texts],
                documents=docs,
                alpha=0.5,
            )
            results = retriever.retrieve("python", k=100)
            assert len(results) == 3, f"Expected all 3 docs, got {len(results)}"
        finally:
            sys.path[:] = old_path

    def test_func_get_document_count(self):
        """get_document_count returns 3 after initializing with 3 documents."""
        parent_dir, pkg_name = self._find_and_add_module()
        old_path = sys.path[:]
        sys.path.insert(0, parent_dir)
        try:
            mod = __import__(
                f"{pkg_name}.hybrid_retriever", fromlist=["HybridRetriever"]
            )
            HybridRetriever = getattr(mod, "HybridRetriever")
            docs = ["python programming guide", "java basics", "cooking recipes"]
            retriever = HybridRetriever(
                embedding_function=lambda texts: [[1.0] * 32 for _ in texts],
                documents=docs,
                alpha=0.5,
            )
            assert retriever.get_document_count() == 3
        finally:
            sys.path[:] = old_path

    def test_func_add_documents_increments_count(self):
        """add_documents increases document count."""
        parent_dir, pkg_name = self._find_and_add_module()
        old_path = sys.path[:]
        sys.path.insert(0, parent_dir)
        try:
            mod = __import__(
                f"{pkg_name}.hybrid_retriever", fromlist=["HybridRetriever"]
            )
            HybridRetriever = getattr(mod, "HybridRetriever")
            docs = ["python programming guide", "java basics", "cooking recipes"]
            retriever = HybridRetriever(
                embedding_function=lambda texts: [[1.0] * 32 for _ in texts],
                documents=docs,
                alpha=0.5,
            )
            initial_count = retriever.get_document_count()
            retriever.add_documents(["new document"])
            assert retriever.get_document_count() == initial_count + 1
        finally:
            sys.path[:] = old_path

    def test_func_empty_retriever_returns_empty(self):
        """Empty retriever returns [] on retrieve."""
        parent_dir, pkg_name = self._find_and_add_module()
        old_path = sys.path[:]
        sys.path.insert(0, parent_dir)
        try:
            mod = __import__(
                f"{pkg_name}.hybrid_retriever", fromlist=["HybridRetriever"]
            )
            HybridRetriever = getattr(mod, "HybridRetriever")
            retriever = HybridRetriever(
                embedding_function=lambda texts: [[1.0] * 32 for _ in texts],
                documents=[],
                alpha=0.5,
            )
            results = retriever.retrieve("python")
            assert results == [], f"Expected empty list, got: {results}"
        finally:
            sys.path[:] = old_path

    def test_func_alpha_too_high_raises_value_error(self):
        """alpha=1.5 raises ValueError."""
        parent_dir, pkg_name = self._find_and_add_module()
        old_path = sys.path[:]
        sys.path.insert(0, parent_dir)
        try:
            mod = __import__(
                f"{pkg_name}.hybrid_retriever", fromlist=["HybridRetriever"]
            )
            HybridRetriever = getattr(mod, "HybridRetriever")
            with pytest.raises(ValueError):
                HybridRetriever(
                    embedding_function=lambda texts: [[1.0] * 32 for _ in texts],
                    documents=["doc"],
                    alpha=1.5,
                )
        finally:
            sys.path[:] = old_path

    def test_func_alpha_negative_raises_value_error(self):
        """alpha=-0.1 raises ValueError."""
        parent_dir, pkg_name = self._find_and_add_module()
        old_path = sys.path[:]
        sys.path.insert(0, parent_dir)
        try:
            mod = __import__(
                f"{pkg_name}.hybrid_retriever", fromlist=["HybridRetriever"]
            )
            HybridRetriever = getattr(mod, "HybridRetriever")
            with pytest.raises(ValueError):
                HybridRetriever(
                    embedding_function=lambda texts: [[1.0] * 32 for _ in texts],
                    documents=["doc"],
                    alpha=-0.1,
                )
        finally:
            sys.path[:] = old_path
