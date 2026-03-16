"""
Test for 'vector-index-tuning' skill — FAISS Vector Index Tuning
Validates that the Agent created optimized FAISS index configurations
with proper parameter tuning and benchmarking.
"""

import os
import subprocess
import pytest


class TestVectorIndexTuning:
    """Verify FAISS vector index tuning implementation."""

    REPO_DIR = "/workspace/faiss"

    # ------------------------------------------------------------------
    # L1: file existence
    # ------------------------------------------------------------------

    def test_tuning_script_exists(self):
        """A vector index tuning script must exist."""
        found = []
        for root, dirs, files in os.walk(self.REPO_DIR):
            for f in files:
                if f.endswith(".py") and (
                    "tun" in f.lower()
                    or "bench" in f.lower()
                    or "index" in f.lower()
                    or "optim" in f.lower()
                ):
                    found.append(os.path.join(root, f))
        assert len(found) >= 1, "No tuning/benchmark script found"

    def test_config_or_readme_exists(self):
        """Configuration or README for tuning must exist."""
        found = False
        for root, dirs, files in os.walk(self.REPO_DIR):
            for f in files:
                if (
                    "tun" in f.lower() or "bench" in f.lower() or "index" in f.lower()
                ) and (f.endswith((".md", ".yml", ".yaml", ".json", ".cfg"))):
                    found = True
                    break
            if found:
                break
        if not found:
            # Check for README in relevant dirs
            for root, dirs, files in os.walk(self.REPO_DIR):
                if "README" in files or "README.md" in files:
                    fpath = os.path.join(root, "README.md")
                    if os.path.isfile(fpath):
                        with open(fpath, "r", errors="ignore") as fh:
                            content = fh.read()
                        if "index" in content.lower() and "tuning" in content.lower():
                            found = True
                            break
        assert found, "No tuning config or README found"

    # ------------------------------------------------------------------
    # L2: content validation
    # ------------------------------------------------------------------

    def _find_tuning_files(self):
        found = []
        for root, dirs, files in os.walk(self.REPO_DIR):
            for f in files:
                if f.endswith(".py") and "node_modules" not in root:
                    fpath = os.path.join(root, f)
                    try:
                        with open(fpath, "r", errors="ignore") as fh:
                            content = fh.read()
                        if "faiss" in content.lower() or "index" in content.lower():
                            found.append(fpath)
                    except OSError:
                        pass
        return found

    def _read_all_tuning(self):
        content = ""
        for fpath in self._find_tuning_files():
            with open(fpath, "r", errors="ignore") as f:
                content += f.read() + "\n"
        return content

    def test_faiss_import(self):
        """Must import faiss library."""
        content = self._read_all_tuning()
        assert (
            "import faiss" in content or "from faiss" in content
        ), "No faiss import found"

    def test_index_factory(self):
        """Must use index_factory or build index."""
        content = self._read_all_tuning()
        factory_patterns = [
            "index_factory",
            "IndexFlatL2",
            "IndexIVFFlat",
            "IndexIVFPQ",
            "IndexHNSW",
            "IndexPQ",
            "IndexScalarQuantizer",
            "GpuIndex",
        ]
        found = sum(1 for p in factory_patterns if p in content)
        assert found >= 2, "Insufficient index construction patterns"

    def test_parameter_sweep(self):
        """Must demonstrate parameter tuning/sweep."""
        content = self._read_all_tuning()
        param_patterns = [
            "nprobe",
            "nlist",
            "M",
            "efConstruction",
            "efSearch",
            "nbits",
            "ParameterSpace",
            "set_search_params",
        ]
        found = sum(1 for p in param_patterns if p in content)
        assert found >= 2, "Insufficient parameter tuning"

    def test_training(self):
        """Must train the index."""
        content = self._read_all_tuning()
        train_patterns = [".train(", "train", "is_trained", "ntotal"]
        found = any(p in content for p in train_patterns)
        assert found, "No index training found"

    def test_search_operation(self):
        """Must perform search operations."""
        content = self._read_all_tuning()
        search_patterns = [
            ".search(",
            "knn_search",
            "range_search",
            "reconstruct",
            "k=",
        ]
        found = any(p in content for p in search_patterns)
        assert found, "No search operation found"

    def test_recall_metric(self):
        """Must measure recall or accuracy."""
        content = self._read_all_tuning()
        recall_patterns = [
            "recall",
            "accuracy",
            "precision",
            "intersection",
            "ground_truth",
            "evaluate",
        ]
        found = any(p in content.lower() for p in recall_patterns)
        assert found, "No recall/accuracy measurement found"

    def test_benchmark_timing(self):
        """Must benchmark query latency."""
        content = self._read_all_tuning()
        timing_patterns = [
            "time.",
            "timeit",
            "perf_counter",
            "latency",
            "qps",
            "throughput",
            "queries per second",
        ]
        found = any(p in content.lower() for p in timing_patterns)
        assert found, "No timing/benchmark measurement found"

    def test_python_scripts_compile(self):
        """All Python tuning scripts must compile."""
        for fpath in self._find_tuning_files():
            result = subprocess.run(
                ["python", "-m", "py_compile", fpath],
                capture_output=True,
                text=True,
                timeout=30,
            )
            assert result.returncode == 0, f"{fpath} compile error:\n{result.stderr}"
