"""
Test for 'similarity-search-patterns' skill — Milvus Similarity Search
Validates that the Agent created similarity search examples with proper
collection setup, indexing, and search patterns in Milvus.
"""

import os
import subprocess
import pytest


class TestSimilaritySearchPatterns:
    """Verify Milvus similarity search implementation."""

    REPO_DIR = "/workspace/milvus"

    # ------------------------------------------------------------------
    # L1: file existence
    # ------------------------------------------------------------------

    def test_search_example_exists(self):
        """A similarity search example file must exist."""
        found = []
        for root, dirs, files in os.walk(self.REPO_DIR):
            for f in files:
                if f.endswith((".py", ".go")) and (
                    "search" in f.lower()
                    or "similar" in f.lower()
                    or "example" in f.lower()
                ):
                    found.append(os.path.join(root, f))
        assert len(found) >= 1, "No similarity search example found"

    def test_documentation_exists(self):
        """README or documentation must exist."""
        found = False
        for root, dirs, files in os.walk(self.REPO_DIR):
            for f in files:
                if f.lower() in ("readme.md",) and (
                    "example" in root.lower() or "search" in root.lower()
                ):
                    found = True
                    break
            if found:
                break
        if not found:
            for root, dirs, files in os.walk(self.REPO_DIR):
                for f in files:
                    if ("search" in f.lower() or "similar" in f.lower()) and f.endswith(
                        ".md"
                    ):
                        found = True
                        break
                if found:
                    break
        assert found, "No documentation found"

    # ------------------------------------------------------------------
    # L2: content validation
    # ------------------------------------------------------------------

    def _find_search_files(self):
        found = []
        for root, dirs, files in os.walk(self.REPO_DIR):
            for f in files:
                if f.endswith((".py", ".go")) and "node_modules" not in root:
                    fpath = os.path.join(root, f)
                    try:
                        with open(fpath, "r", errors="ignore") as fh:
                            content = fh.read()
                        if any(
                            p in content.lower()
                            for p in [
                                "milvus",
                                "collection",
                                "similarity",
                                "vector",
                                "search",
                            ]
                        ):
                            found.append(fpath)
                    except OSError:
                        pass
        return found

    def _read_all_search(self):
        content = ""
        for fpath in self._find_search_files():
            with open(fpath, "r", errors="ignore") as f:
                content += f.read() + "\n"
        return content

    def test_collection_creation(self):
        """Must create a Milvus collection."""
        content = self._read_all_search()
        coll_patterns = [
            "Collection",
            "create_collection",
            "CollectionSchema",
            "FieldSchema",
            "CreateCollection",
        ]
        found = any(p in content for p in coll_patterns)
        assert found, "No collection creation found"

    def test_index_building(self):
        """Must build a vector index."""
        content = self._read_all_search()
        index_patterns = [
            "create_index",
            "IndexType",
            "IVF_FLAT",
            "IVF_SQ8",
            "HNSW",
            "index_params",
            "CreateIndex",
            "FLAT",
        ]
        found = any(p in content for p in index_patterns)
        assert found, "No vector index creation found"

    def test_vector_insertion(self):
        """Must insert vectors into collection."""
        content = self._read_all_search()
        insert_patterns = ["insert", "Import", "upsert", "Insert"]
        found = any(p in content for p in insert_patterns)
        assert found, "No vector insertion found"

    def test_search_operation(self):
        """Must perform similarity search."""
        content = self._read_all_search()
        search_patterns = ["search", "Search", "query", "Query", "ann_search", "knn"]
        found = any(p in content for p in search_patterns)
        assert found, "No search operation found"

    def test_distance_metric(self):
        """Must specify a distance metric."""
        content = self._read_all_search()
        metric_patterns = [
            "L2",
            "IP",
            "COSINE",
            "metric_type",
            "MetricType",
            "euclidean",
            "cosine",
            "inner_product",
        ]
        found = any(p in content for p in metric_patterns)
        assert found, "No distance metric specified"

    def test_search_params(self):
        """Must configure search parameters."""
        content = self._read_all_search()
        param_patterns = [
            "search_params",
            "nprobe",
            "ef",
            "top_k",
            "limit",
            "output_fields",
            "anns_field",
        ]
        found = any(p in content for p in param_patterns)
        assert found, "No search parameters found"

    def test_schema_definition(self):
        """Must define collection schema with vector field."""
        content = self._read_all_search()
        schema_patterns = [
            "DataType.FLOAT_VECTOR",
            "dim=",
            "FloatVector",
            "BinaryVector",
            "vector_field",
            "VARCHAR",
            "INT64",
        ]
        found = sum(1 for p in schema_patterns if p in content)
        assert found >= 2, "Insufficient schema definition"

    def test_python_scripts_compile(self):
        """Python search files must compile."""
        for fpath in self._find_search_files():
            if fpath.endswith(".py"):
                result = subprocess.run(
                    ["python", "-m", "py_compile", fpath],
                    capture_output=True,
                    text=True,
                    timeout=30,
                )
                assert (
                    result.returncode == 0
                ), f"{fpath} compile error:\n{result.stderr}"
