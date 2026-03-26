"""
Test for 'vector-index-tuning' skill — FAISS Vector Index Benchmark
Validates that the Agent created a vector index benchmark script using
FAISS with multiple index types, recall/latency measurement, and comparison.
"""

import os
import re
import subprocess

import pytest

from _dependency_utils import ensure_python_dependencies


@pytest.fixture(scope="module", autouse=True)
def _ensure_repo_dependencies():
    ensure_python_dependencies(TestVectorIndexTuning.REPO_DIR)


class TestVectorIndexTuning:
    """Verify FAISS vector index benchmark script."""

    REPO_DIR = "/workspace/faiss"

    def _read(self, *parts):
        fpath = os.path.join(self.REPO_DIR, *parts)
        assert os.path.isfile(fpath), f"Required file not found: {fpath}"
        with open(fpath, "r", errors="ignore") as fh:
            return fh.read()

    def _find_benchmark_script(self):
        """Find the benchmark script in common locations."""
        candidates = [
            "tutorial/python/index_tuning_benchmark.py",
            "benchmarks/index_benchmark.py",
            "benchmarks/benchmark.py",
            "benchmark/index_benchmark.py",
            "examples/benchmark.py",
            "examples/index_benchmark.py",
            "index_benchmark.py",
            "benchmark.py",
            "benchmarks/vector_index_benchmark.py",
        ]
        for rel in candidates:
            fpath = os.path.join(self.REPO_DIR, rel)
            if os.path.isfile(fpath):
                return fpath
        # Fallback search
        for root, _dirs, files in os.walk(self.REPO_DIR):
            for f in files:
                if f.endswith(".py") and "benchmark" in f.lower():
                    return os.path.join(root, f)
        pytest.fail("Benchmark script not found in expected locations")

    # ------------------------------------------------------------------
    # L1: File existence and syntax
    # ------------------------------------------------------------------

    def test_benchmark_script_exists(self):
        """A FAISS benchmark Python script must exist."""
        self._find_benchmark_script()

    def test_benchmark_compiles(self):
        """Benchmark script must be syntactically valid Python."""
        script = self._find_benchmark_script()
        result = subprocess.run(
            ["python", "-m", "py_compile", script],
            capture_output=True,
            text=True,
            timeout=30,
        )
        assert result.returncode == 0, f"Syntax error:\n{result.stderr}"

    def test_imports_faiss(self):
        """Script must import faiss library."""
        script = self._find_benchmark_script()
        with open(script, "r", errors="ignore") as fh:
            content = fh.read()
        assert re.search(
            r"import\s+faiss|from\s+faiss", content
        ), "Script does not import faiss"

    # ------------------------------------------------------------------
    # L1: Multiple index types
    # ------------------------------------------------------------------

    def test_uses_at_least_two_index_types(self):
        """Script must build at least 2 different index types."""
        script = self._find_benchmark_script()
        with open(script, "r", errors="ignore") as fh:
            content = fh.read()
        index_types = [
            r"IndexFlat",
            r"IndexIVF",
            r"IndexHNSW",
            r"IndexPQ",
            r"IndexScalarQuantizer",
            r"IndexLSH",
            r"index_factory.*Flat",
            r"index_factory.*IVF",
            r"index_factory.*HNSW",
            r"index_factory.*PQ",
            r"Flat",
            r"IVF",
            r"HNSW",
            r"PQ",
        ]
        found = set()
        for p in index_types:
            if re.search(p, content):
                found.add(p.split(".")[-1] if "." in p else p)
        assert (
            len(found) >= 2
        ), f"Only {len(found)} index type(s) found: {found} — need at least 2"

    def test_configures_tuning_knobs(self):
        """Script must vary tuning parameters (nprobe, efSearch, etc.)."""
        script = self._find_benchmark_script()
        with open(script, "r", errors="ignore") as fh:
            content = fh.read()
        knobs = [
            r"nprobe",
            r"efSearch",
            r"efConstruction",
            r"nlist",
            r"nbits",
            r"m\b",
            r"M\b",
        ]
        found = sum(1 for p in knobs if re.search(p, content))
        assert (
            found >= 1
        ), "Script does not configure tuning knobs like nprobe or efSearch"

    # ------------------------------------------------------------------
    # L2: Measurement
    # ------------------------------------------------------------------

    def test_measures_recall(self):
        """Script must measure recall@k quality metric."""
        script = self._find_benchmark_script()
        with open(script, "r", errors="ignore") as fh:
            content = fh.read()
        patterns = [
            r"recall",
            r"recall@",
            r"recall_at",
            r"intersection",
            r"ground.truth",
        ]
        assert any(
            re.search(p, content, re.IGNORECASE) for p in patterns
        ), "Script does not measure recall"

    def test_measures_latency(self):
        """Script must measure query latency."""
        script = self._find_benchmark_script()
        with open(script, "r", errors="ignore") as fh:
            content = fh.read()
        patterns = [
            r"latency",
            r"time\.time",
            r"time\.perf",
            r"timeit",
            r"elapsed",
            r"duration",
            r"qps",
            r"queries.per.second",
        ]
        assert any(
            re.search(p, content, re.IGNORECASE) for p in patterns
        ), "Script does not measure latency"

    # ------------------------------------------------------------------
    # L2: Comparison output
    # ------------------------------------------------------------------

    def test_produces_comparison_table(self):
        """Script must output a comparison table or structured results."""
        script = self._find_benchmark_script()
        with open(script, "r", errors="ignore") as fh:
            content = fh.read()
        patterns = [
            r"table",
            r"print.*result",
            r"DataFrame",
            r"csv",
            r"json\.dump",
            r"format.*\|",
            r"tabulate",
            r"report",
            r"comparison",
        ]
        assert any(
            re.search(p, content, re.IGNORECASE) for p in patterns
        ), "Script does not produce a comparison table"

    def test_compares_indexes_side_by_side(self):
        """Script must produce a side-by-side comparison of index types."""
        script = self._find_benchmark_script()
        with open(script, "r", errors="ignore") as fh:
            content = fh.read()
        # Should iterate/collect results for multiple indexes
        patterns = [
            r"for.*index.*in",
            r"results\[",
            r"results\.append",
            r"for.*config.*in",
            r"benchmark_results",
        ]
        assert any(
            re.search(p, content, re.IGNORECASE) for p in patterns
        ), "Script does not compare multiple indexes"

    def test_generates_random_data(self):
        """Script must generate or load test vector data."""
        script = self._find_benchmark_script()
        with open(script, "r", errors="ignore") as fh:
            content = fh.read()
        patterns = [
            r"np\.random",
            r"numpy\.random",
            r"random\.rand",
            r"randn",
            r"load.*data",
            r"generate.*vector",
            r"fvecs",
            r"dataset",
        ]
        assert any(
            re.search(p, content, re.IGNORECASE) for p in patterns
        ), "Script does not generate or load vectors"

    def test_has_main_entry(self):
        """Benchmark script should have a __main__ entry point."""
        script = self._find_benchmark_script()
        with open(script, "r", errors="ignore") as fh:
            content = fh.read()
        assert re.search(
            r'if\s+__name__\s*==\s*["\']__main__["\']', content
        ), "Script lacks __main__ entry point"
