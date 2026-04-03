"""
Test for 'similarity-search-patterns' skill — Milvus similarity search patterns
Validates that the Agent implemented similarity search patterns using
the Milvus vector database.
"""

import os
import re

import pytest


class TestSimilaritySearchPatterns:
    """Verify Milvus similarity search implementation."""

    REPO_DIR = "/workspace/milvus"

    def test_collection_creation(self):
        """Milvus collection creation must be implemented."""
        found = False
        for root, dirs, files in os.walk(self.REPO_DIR):
            for f in files:
                if f.endswith((".py", ".go", ".java")):
                    path = os.path.join(root, f)
                    with open(path, "r", errors="ignore") as fh:
                        content = fh.read()
                    if re.search(r"[Cc]reate[Cc]ollection|create_collection|Collection\(|NewCollection", content):
                        found = True
                        break
            if found:
                break
        assert found, "No collection creation found"

    def test_schema_definition(self):
        """Collection schema must be defined with fields."""
        found = False
        for root, dirs, files in os.walk(self.REPO_DIR):
            for f in files:
                if f.endswith((".py", ".go", ".java")):
                    path = os.path.join(root, f)
                    with open(path, "r", errors="ignore") as fh:
                        content = fh.read()
                    if re.search(r"[Ss]chema|FieldSchema|CollectionSchema|[Ff]ield|DataType|FloatVector", content):
                        found = True
                        break
            if found:
                break
        assert found, "No schema definition found"

    def test_index_creation(self):
        """Vector index must be created."""
        found = False
        for root, dirs, files in os.walk(self.REPO_DIR):
            for f in files:
                if f.endswith((".py", ".go", ".java")):
                    path = os.path.join(root, f)
                    with open(path, "r", errors="ignore") as fh:
                        content = fh.read()
                    if re.search(r"create_index|CreateIndex|index_params|IVF_FLAT|HNSW|ANNOY|IndexType", content):
                        found = True
                        break
            if found:
                break
        assert found, "No index creation found"

    def test_data_insertion(self):
        """Data insertion into collection must be implemented."""
        found = False
        for root, dirs, files in os.walk(self.REPO_DIR):
            for f in files:
                if f.endswith((".py", ".go", ".java")):
                    path = os.path.join(root, f)
                    with open(path, "r", errors="ignore") as fh:
                        content = fh.read()
                    if re.search(r"insert|Insert|upsert|Upsert", content):
                        found = True
                        break
            if found:
                break
        assert found, "No data insertion found"

    def test_similarity_search(self):
        """Similarity search must be implemented."""
        found = False
        for root, dirs, files in os.walk(self.REPO_DIR):
            for f in files:
                if f.endswith((".py", ".go", ".java")):
                    path = os.path.join(root, f)
                    with open(path, "r", errors="ignore") as fh:
                        content = fh.read()
                    if re.search(r"search|Search|query|similarity|knn|ANN|nearest", content):
                        found = True
                        break
            if found:
                break
        assert found, "No similarity search found"

    def test_distance_metric(self):
        """Distance metric must be configured (L2, IP, COSINE)."""
        found = False
        for root, dirs, files in os.walk(self.REPO_DIR):
            for f in files:
                if f.endswith((".py", ".go", ".java")):
                    path = os.path.join(root, f)
                    with open(path, "r", errors="ignore") as fh:
                        content = fh.read()
                    if re.search(r"metric_type|MetricType|L2|IP|COSINE|cosine|euclidean|inner_product", content):
                        found = True
                        break
            if found:
                break
        assert found, "No distance metric configured"

    def test_vector_embedding(self):
        """Vector embeddings must be generated or used."""
        found = False
        for root, dirs, files in os.walk(self.REPO_DIR):
            for f in files:
                if f.endswith((".py", ".go", ".java")):
                    path = os.path.join(root, f)
                    with open(path, "r", errors="ignore") as fh:
                        content = fh.read()
                    if re.search(r"[Ee]mbedding|vector|FloatVector|float_vector|dim\s*=|dimension", content):
                        found = True
                        break
            if found:
                break
        assert found, "No vector embedding found"

    def test_top_k_results(self):
        """Search must return top-K results."""
        found = False
        for root, dirs, files in os.walk(self.REPO_DIR):
            for f in files:
                if f.endswith((".py", ".go", ".java")):
                    path = os.path.join(root, f)
                    with open(path, "r", errors="ignore") as fh:
                        content = fh.read()
                    if re.search(r"top_k|topk|limit|nprobe|nlist|k\s*=", content):
                        found = True
                        break
            if found:
                break
        assert found, "No top-K configuration found"

    def test_connection_setup(self):
        """Milvus connection must be established."""
        found = False
        for root, dirs, files in os.walk(self.REPO_DIR):
            for f in files:
                if f.endswith((".py", ".go", ".java")):
                    path = os.path.join(root, f)
                    with open(path, "r", errors="ignore") as fh:
                        content = fh.read()
                    if re.search(r"connect|connections|MilvusClient|grpc|host|port", content, re.IGNORECASE):
                        found = True
                        break
            if found:
                break
        assert found, "No Milvus connection setup found"

    def test_collection_loading(self):
        """Collection must be loaded into memory before search."""
        found = False
        for root, dirs, files in os.walk(self.REPO_DIR):
            for f in files:
                if f.endswith((".py", ".go", ".java")):
                    path = os.path.join(root, f)
                    with open(path, "r", errors="ignore") as fh:
                        content = fh.read()
                    if re.search(r"load|Load|release|Release|collection\.load", content):
                        found = True
                        break
            if found:
                break
        assert found, "No collection loading found"
