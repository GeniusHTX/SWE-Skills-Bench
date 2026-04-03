"""
Test for 'spark-optimization' skill — Spark Optimization
Validates Spark optimization functions: optimize_join, repartition_for_writes,
compute_aggregations, cache_with_strategy, detect_skew via AST/static analysis.
"""

import os
import re
import ast
import glob
import pytest


class TestSparkOptimization:
    """Tests for Spark optimization patterns in the spark repo."""

    REPO_DIR = "/workspace/spark"

    def _read(self, relpath):
        full = os.path.join(self.REPO_DIR, relpath)
        with open(full, "r", errors="ignore") as f:
            return f.read()

    def _find_spark_opt_files(self):
        """Find all spark_optimizations*.py and examples/**/*.py files."""
        patterns = [
            os.path.join(self.REPO_DIR, "**", "spark_optimizations*.py"),
            os.path.join(self.REPO_DIR, "examples", "**", "*.py"),
        ]
        files = []
        for p in patterns:
            files.extend(glob.glob(p, recursive=True))
        return files

    def _get_all_content(self):
        """Read and concatenate all relevant source files."""
        files = self._find_spark_opt_files()
        assert len(files) > 0, "No spark optimization files found"
        contents = []
        for f in files:
            rel = os.path.relpath(f, self.REPO_DIR)
            contents.append(self._read(rel))
        return "\n".join(contents)

    def _parse_all_functions(self):
        """Parse all source files and return set of top-level function names."""
        files = self._find_spark_opt_files()
        assert len(files) > 0, "No spark optimization files found"
        func_names = set()
        for f in files:
            rel = os.path.relpath(f, self.REPO_DIR)
            content = self._read(rel)
            try:
                tree = ast.parse(content)
                for node in ast.walk(tree):
                    if isinstance(node, ast.FunctionDef):
                        func_names.add(node.name)
            except SyntaxError:
                pass
        return func_names

    # --- File Path Checks ---

    def test_spark_optimization_files_exist(self):
        """Verifies that spark optimization source files exist."""
        files = self._find_spark_opt_files()
        assert (
            len(files) > 0
        ), "No spark_optimizations*.py or examples/**/*.py files found"

    # --- Semantic Checks (AST analysis) ---

    def test_sem_optimize_join_function_defined(self):
        """optimize_join function is defined."""
        func_names = self._parse_all_functions()
        assert (
            "optimize_join" in func_names
        ), f"optimize_join not found. Functions: {func_names}"

    def test_sem_repartition_for_writes_function_defined(self):
        """repartition_for_writes function is defined."""
        func_names = self._parse_all_functions()
        assert (
            "repartition_for_writes" in func_names
        ), f"repartition_for_writes not found. Functions: {func_names}"

    def test_sem_compute_aggregations_function_defined(self):
        """compute_aggregations function is defined."""
        func_names = self._parse_all_functions()
        assert (
            "compute_aggregations" in func_names
        ), f"compute_aggregations not found. Functions: {func_names}"

    def test_sem_cache_with_strategy_function_defined(self):
        """cache_with_strategy function is defined."""
        func_names = self._parse_all_functions()
        assert (
            "cache_with_strategy" in func_names
        ), f"cache_with_strategy not found. Functions: {func_names}"

    def test_sem_detect_skew_function_defined(self):
        """detect_skew function is defined."""
        func_names = self._parse_all_functions()
        assert (
            "detect_skew" in func_names
        ), f"detect_skew not found. Functions: {func_names}"

    # --- Functional Checks (static content analysis) ---

    def test_func_optimize_join_uses_broadcast(self):
        """optimize_join uses broadcast for small table optimization."""
        content = self._get_all_content()
        assert (
            "broadcast" in content.lower()
        ), "broadcast not found in spark optimization code"

    def test_func_cache_with_strategy_uses_storage_level(self):
        """cache_with_strategy references StorageLevel."""
        content = self._get_all_content()
        assert "StorageLevel" in content, "StorageLevel not found in code"

    def test_func_cache_with_strategy_uses_memory_and_disk(self):
        """cache_with_strategy references MEMORY_AND_DISK."""
        content = self._get_all_content()
        assert "MEMORY_AND_DISK" in content, "MEMORY_AND_DISK not found in code"

    def test_func_repartition_uses_repartition_or_partition_by(self):
        """repartition_for_writes uses repartition or partitionBy."""
        content = self._get_all_content()
        has_repartition = "repartition" in content
        has_partition_by = "partitionBy" in content
        assert (
            has_repartition or has_partition_by
        ), "Neither repartition nor partitionBy found"

    def test_func_detect_skew_handles_value_error(self):
        """detect_skew handles or raises ValueError for invalid inputs."""
        content = self._get_all_content()
        assert "ValueError" in content, "ValueError not found in code"

    def test_func_compute_aggregations_uses_agg_functions(self):
        """compute_aggregations uses aggregate functions (sum, avg, count, min, max)."""
        content = self._get_all_content()
        agg_funcs = ["sum", "avg", "count", "min", "max"]
        found = [f for f in agg_funcs if f in content.lower()]
        assert (
            len(found) >= 2
        ), f"Expected at least 2 aggregate functions, found: {found}"

    def test_func_optimize_join_has_threshold_logic(self):
        """optimize_join contains threshold or size-based logic for broadcast decisions."""
        content = self._get_all_content()
        has_threshold = re.search(r"threshold|size|bytes|mb|MB", content)
        assert has_threshold, "No threshold/size-based logic found in optimize_join"

    def test_func_repartition_has_num_partitions(self):
        """repartition_for_writes accepts num_partitions parameter."""
        content = self._get_all_content()
        assert re.search(
            r"num_partitions|numPartitions|n_partitions", content
        ), "No num_partitions parameter found"

    def test_func_all_functions_have_docstrings(self):
        """All optimization functions have docstrings."""
        files = self._find_spark_opt_files()
        assert len(files) > 0
        target_funcs = {
            "optimize_join",
            "repartition_for_writes",
            "compute_aggregations",
            "cache_with_strategy",
            "detect_skew",
        }
        for f in files:
            rel = os.path.relpath(f, self.REPO_DIR)
            content = self._read(rel)
            try:
                tree = ast.parse(content)
                for node in ast.walk(tree):
                    if isinstance(node, ast.FunctionDef) and node.name in target_funcs:
                        docstring = ast.get_docstring(node)
                        assert docstring is not None, f"{node.name} has no docstring"
            except SyntaxError:
                pass
