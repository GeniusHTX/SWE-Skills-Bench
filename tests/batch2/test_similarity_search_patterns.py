"""
Test for 'similarity-search-patterns' skill — Vector Similarity Search
Validates that the Agent created a similarity search demo using Milvus
with collection management, vector operations, multiple distance metrics,
and filtered search capabilities.
"""

import os
import re
import subprocess

import pytest

from _dependency_utils import ensure_python_dependencies


@pytest.fixture(scope="module", autouse=True)
def _ensure_repo_dependencies():
    ensure_python_dependencies(TestSimilaritySearchPatterns.REPO_DIR)


class TestSimilaritySearchPatterns:
    """Verify Milvus similarity search demo."""

    REPO_DIR = "/workspace/milvus"

    def _read(self, *parts):
        fpath = os.path.join(self.REPO_DIR, *parts)
        assert os.path.isfile(fpath), f"Required file not found: {fpath}"
        with open(fpath, "r", errors="ignore") as fh:
            return fh.read()

    def _find_demo_script(self):
        """Find the similarity search demo script."""
        candidates = [
            "examples/similarity_search_demo.py",
            "examples/search_demo.py",
            "similarity_search_demo.py",
            "search_demo.py",
            "demo/similarity_search.py",
            "examples/demo.py",
        ]
        for rel in candidates:
            fpath = os.path.join(self.REPO_DIR, rel)
            if os.path.isfile(fpath):
                return fpath
        # Fallback search
        for root, _dirs, files in os.walk(self.REPO_DIR):
            for f in files:
                if f.endswith(".py") and (
                    "similar" in f.lower() or "search" in f.lower()
                ):
                    full = os.path.join(root, f)
                    with open(full, "r", errors="ignore") as fh:
                        if "milvus" in fh.read().lower():
                            return full
        pytest.fail("Similarity search demo script not found")

    # ------------------------------------------------------------------
    # L1: File existence and syntax
    # ------------------------------------------------------------------

    def test_demo_script_exists(self):
        """A Milvus similarity search demo script must exist."""
        self._find_demo_script()

    def test_script_compiles(self):
        """Demo script must be syntactically valid Python."""
        script = self._find_demo_script()
        result = subprocess.run(
            ["python", "-m", "py_compile", script],
            capture_output=True,
            text=True,
            timeout=30,
        )
        assert result.returncode == 0, f"Syntax error:\n{result.stderr}"

    def test_imports_pymilvus(self):
        """Script must import pymilvus or milvus client."""
        script = self._find_demo_script()
        with open(script, "r", errors="ignore") as fh:
            content = fh.read()
        patterns = [
            r"from\s+pymilvus",
            r"import\s+pymilvus",
            r"from\s+milvus",
            r"import\s+milvus",
            r"MilvusClient",
        ]
        assert any(
            re.search(p, content) for p in patterns
        ), "Script does not import pymilvus or milvus client"

    # ------------------------------------------------------------------
    # L1: Collection management
    # ------------------------------------------------------------------

    def test_creates_collection(self):
        """Script must create a Milvus collection."""
        script = self._find_demo_script()
        with open(script, "r", errors="ignore") as fh:
            content = fh.read()
        patterns = [
            r"create_collection",
            r"Collection\(",
            r"CollectionSchema",
            r"FieldSchema",
        ]
        assert any(
            re.search(p, content) for p in patterns
        ), "Script does not create a collection"

    def test_defines_vector_field(self):
        """Collection schema must include a vector field."""
        script = self._find_demo_script()
        with open(script, "r", errors="ignore") as fh:
            content = fh.read()
        patterns = [
            r"FLOAT_VECTOR",
            r"FloatVector",
            r"dim\s*=",
            r"dimension",
            r"DataType.*FLOAT_VECTOR",
        ]
        assert any(
            re.search(p, content) for p in patterns
        ), "Collection schema does not define a vector field"

    # ------------------------------------------------------------------
    # L2: Data insertion
    # ------------------------------------------------------------------

    def test_inserts_vectors(self):
        """Script must insert vectors into the collection."""
        script = self._find_demo_script()
        with open(script, "r", errors="ignore") as fh:
            content = fh.read()
        patterns = [r"\.insert\(", r"insert_data", r"bulk_insert", r"upsert"]
        assert any(
            re.search(p, content) for p in patterns
        ), "Script does not insert vectors into collection"

    def test_includes_metadata(self):
        """Inserted data must include metadata/scalar fields."""
        script = self._find_demo_script()
        with open(script, "r", errors="ignore") as fh:
            content = fh.read()
        patterns = [
            r"VARCHAR",
            r"INT64",
            r"metadata",
            r"scalar",
            r"label",
            r"category",
            r"title",
            r"description",
        ]
        assert any(
            re.search(p, content, re.IGNORECASE) for p in patterns
        ), "Inserted data does not include metadata fields"

    # ------------------------------------------------------------------
    # L2: Distance metrics
    # ------------------------------------------------------------------

    def test_supports_multiple_distance_metrics(self):
        """Script must use or reference at least 2 distance metrics."""
        script = self._find_demo_script()
        with open(script, "r", errors="ignore") as fh:
            content = fh.read()
        metrics = [
            r"L2",
            r"IP",
            r"COSINE",
            r"cosine",
            r"euclidean",
            r"inner.product",
            r"HAMMING",
            r"JACCARD",
        ]
        found = sum(1 for p in metrics if re.search(p, content, re.IGNORECASE))
        assert (
            found >= 2
        ), f"Only {found} distance metric(s) referenced — need at least 2"

    # ------------------------------------------------------------------
    # L2: Search operations
    # ------------------------------------------------------------------

    def test_performs_similarity_search(self):
        """Script must perform similarity search queries."""
        script = self._find_demo_script()
        with open(script, "r", errors="ignore") as fh:
            content = fh.read()
        patterns = [
            r"\.search\(",
            r"search_params",
            r"query_vector",
            r"top_k",
            r"limit",
        ]
        assert any(
            re.search(p, content) for p in patterns
        ), "Script does not perform similarity search"

    def test_creates_index(self):
        """Script must create a vector index."""
        script = self._find_demo_script()
        with open(script, "r", errors="ignore") as fh:
            content = fh.read()
        patterns = [
            r"create_index",
            r"index_params",
            r"IndexType",
            r"IVF_FLAT",
            r"HNSW",
            r"IVF_SQ8",
            r"ANNOY",
        ]
        assert any(
            re.search(p, content) for p in patterns
        ), "Script does not create a vector index"

    def test_supports_filtered_search(self):
        """Script must support filtered/hybrid search."""
        script = self._find_demo_script()
        with open(script, "r", errors="ignore") as fh:
            content = fh.read()
        patterns = [
            r"filter",
            r"expr\s*=",
            r"boolean_expr",
            r"query.*expr",
            r"hybrid.*search",
            r"scalar.*filter",
        ]
        assert any(
            re.search(p, content, re.IGNORECASE) for p in patterns
        ), "Script does not support filtered search"

    def test_displays_search_results(self):
        """Script must display or return search results with scores."""
        script = self._find_demo_script()
        with open(script, "r", errors="ignore") as fh:
            content = fh.read()
        patterns = [r"distance", r"score", r"print.*result", r"hits", r"top.*result"]
        assert any(
            re.search(p, content, re.IGNORECASE) for p in patterns
        ), "Script does not display search results"

    def test_has_main_entry(self):
        """Script should have a __main__ entry point."""
        script = self._find_demo_script()
        with open(script, "r", errors="ignore") as fh:
            content = fh.read()
        assert re.search(
            r'if\s+__name__\s*==\s*["\']__main__["\']', content
        ), "Script lacks __main__ entry point"
