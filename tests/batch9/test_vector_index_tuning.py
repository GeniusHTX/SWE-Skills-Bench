"""
Test for 'vector-index-tuning' skill — FAISS Vector Index Tuning
Validates IndexFactory, IndexTrainer, RecallBenchmark, IndexSerializer,
Flat/IVF index creation, recall measurement, and serialization round-trip.
"""

import os
import subprocess
import sys

import pytest


class TestVectorIndexTuning:
    """Verify FAISS vector index tuning: factory, trainer, benchmark, serializer."""

    REPO_DIR = "/workspace/faiss"

    # ── helpers ──────────────────────────────────────────────────────────

    @staticmethod
    def _read_file(path: str) -> str:
        try:
            with open(path, "r", errors="ignore") as fh:
                return fh.read()
        except OSError:
            return ""

    def _vi(self, *parts) -> str:
        return os.path.join(self.REPO_DIR, "examples", "vector_index", *parts)

    def _install_deps(self):
        try:
            import faiss  # noqa: F401
        except ImportError:
            subprocess.run(
                [sys.executable, "-m", "pip", "install", "faiss-cpu", "numpy"],
                capture_output=True, timeout=120,
            )

    # ── file_path_check ──────────────────────────────────────────────────

    def test_factory_trainer_init_exist(self):
        """__init__.py, factory.py, trainer.py must exist."""
        for name in ("__init__.py", "factory.py", "trainer.py"):
            path = self._vi(name)
            assert os.path.isfile(path), f"{path} does not exist"

    def test_benchmark_and_serializer_exist(self):
        """benchmark.py and serializer.py must exist."""
        for name in ("benchmark.py", "serializer.py"):
            path = self._vi(name)
            assert os.path.isfile(path), f"{path} does not exist"

    def test_test_file_exists(self):
        """tests/test_vector_index.py must exist."""
        path = os.path.join(self.REPO_DIR, "tests", "test_vector_index.py")
        assert os.path.isfile(path), f"{path} not found"

    # ── semantic_check ───────────────────────────────────────────────────

    def test_factory_create_method(self):
        """factory.py must define IndexFactory.create(spec, dim)."""
        path = self._vi("factory.py")
        if not os.path.isfile(path):
            pytest.skip("factory.py not found")
        content = self._read_file(path)
        assert "IndexFactory" in content, "IndexFactory not defined"
        assert "create" in content, "create method not found"
        assert "faiss" in content, "faiss not referenced"

    def test_trainer_calls_index_train(self):
        """trainer.py must call index.train()."""
        path = self._vi("trainer.py")
        if not os.path.isfile(path):
            pytest.skip("trainer.py not found")
        content = self._read_file(path)
        assert "train" in content, "train method not found"

    def test_benchmark_returns_recall(self):
        """benchmark.py must define RecallBenchmark.measure."""
        path = self._vi("benchmark.py")
        if not os.path.isfile(path):
            pytest.skip("benchmark.py not found")
        content = self._read_file(path)
        assert "RecallBenchmark" in content, "RecallBenchmark not defined"
        assert "measure" in content, "measure method not found"

    def test_serializer_uses_faiss_io(self):
        """serializer.py must use faiss.write_index/read_index, not pickle."""
        path = self._vi("serializer.py")
        if not os.path.isfile(path):
            pytest.skip("serializer.py not found")
        content = self._read_file(path)
        assert "write_index" in content, "faiss.write_index not found"
        assert "read_index" in content, "faiss.read_index not found"
        assert "pickle" not in content, "pickle should not be used for FAISS indices"

    # ── functional_check ─────────────────────────────────────────────────

    def test_flat_index_creation(self):
        """IndexFactory.create('Flat', 64) must return IndexFlatL2."""
        self._install_deps()
        try:
            import faiss
            sys.path.insert(0, self.REPO_DIR)
            from examples.vector_index.factory import IndexFactory
        except ImportError:
            pytest.skip("Cannot import IndexFactory or faiss")
        idx = IndexFactory.create("Flat", 64)
        assert isinstance(idx, faiss.IndexFlatL2)

    def test_ivf_add_before_train_raises(self):
        """IVF index add() before train() must raise RuntimeError."""
        self._install_deps()
        try:
            import faiss
            import numpy as np
            sys.path.insert(0, self.REPO_DIR)
            from examples.vector_index.factory import IndexFactory
        except ImportError:
            pytest.skip("Cannot import required modules")
        idx = IndexFactory.create("IVF8,Flat", 64)
        with pytest.raises(RuntimeError):
            idx.add(np.random.rand(100, 64).astype("float32"))

    def test_flat_recall_at_1(self):
        """Flat index recall@1 for queries equal to indexed vectors must be 1.0."""
        self._install_deps()
        try:
            import numpy as np
            sys.path.insert(0, self.REPO_DIR)
            from examples.vector_index.factory import IndexFactory
            from examples.vector_index.benchmark import RecallBenchmark
        except ImportError:
            pytest.skip("Cannot import required modules")
        vecs = np.random.rand(100, 64).astype("float32")
        idx = IndexFactory.create("Flat", 64)
        idx.add(vecs)
        recall = RecallBenchmark().measure(idx, vecs, list(range(100)), k=1)
        assert abs(recall - 1.0) < 0.01, f"Flat recall@1 should be 1.0, got {recall}"

    def test_serialization_roundtrip(self, tmp_path):
        """Serialized and reloaded index must have same ntotal."""
        self._install_deps()
        try:
            import numpy as np
            sys.path.insert(0, self.REPO_DIR)
            from examples.vector_index.factory import IndexFactory
            from examples.vector_index.serializer import IndexSerializer
        except ImportError:
            pytest.skip("Cannot import required modules")
        idx = IndexFactory.create("Flat", 64)
        idx.add(np.random.rand(100, 64).astype("float32"))
        path = str(tmp_path / "test.faiss")
        IndexSerializer().save(idx, path)
        reloaded = IndexSerializer().load(path)
        assert reloaded.ntotal == 100

    def test_load_nonexistent_raises(self):
        """Loading non-existent file must raise FileNotFoundError or RuntimeError."""
        self._install_deps()
        try:
            sys.path.insert(0, self.REPO_DIR)
            from examples.vector_index.serializer import IndexSerializer
        except ImportError:
            pytest.skip("Cannot import IndexSerializer")
        with pytest.raises((FileNotFoundError, RuntimeError)):
            IndexSerializer().load("/nonexistent/path/index.faiss")
