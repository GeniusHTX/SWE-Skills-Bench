"""
Tests for 'similarity-search-patterns' skill.
Generated from benchmark case definitions for similarity-search-patterns.
"""

import ast
import base64
import glob
import json
import os
import py_compile
import re
import subprocess
import textwrap

import pytest

try:
    import yaml
except ModuleNotFoundError:
    yaml = None


class TestSimilaritySearchPatterns:
    """Verify the similarity-search-patterns skill output."""

    REPO_DIR = '/workspace/milvus'


    # ── helpers ──────────────────────────────────────────────

    _SETUP_CACHE: dict = {}

    @staticmethod
    def _repo_path(rel: str) -> str:
        return os.path.join(TestSimilaritySearchPatterns.REPO_DIR, rel)

    @staticmethod
    def _safe_read(path: str) -> str:
        with open(path, "r", encoding="utf-8", errors="ignore") as fh:
            return fh.read()

    @staticmethod
    def _load_yaml(path: str):
        if yaml is None:
            pytest.skip("PyYAML not available")
        with open(path, "r", encoding="utf-8", errors="ignore") as fh:
            return yaml.safe_load(fh)

    @staticmethod
    def _load_json(path: str):
        with open(path, "r", encoding="utf-8", errors="ignore") as fh:
            return json.load(fh)

    @classmethod
    def _run_in_repo(cls, script: str, timeout: int = 120) -> subprocess.CompletedProcess:
        return subprocess.run(
            ["python", "-c", textwrap.dedent(script)],
            cwd=cls.REPO_DIR,
            capture_output=True,
            text=True,
            timeout=timeout,
        )

    @classmethod
    def _run_cmd(cls, command, args=None, timeout=120):
        args = args or []
        if isinstance(command, str) and args:
            return subprocess.run(
                [command, *args],
                cwd=cls.REPO_DIR,
                capture_output=True,
                text=True,
                timeout=timeout,
            )
        return subprocess.run(
            command if isinstance(command, list) else command,
            cwd=cls.REPO_DIR,
            shell=isinstance(command, str),
            capture_output=True,
            text=True,
            timeout=timeout,
        )

    @classmethod
    def _ensure_setup(cls, label, setup_cmds, fallback):
        if not setup_cmds:
            return
        key = tuple(setup_cmds)
        if key in cls._SETUP_CACHE:
            ok, msg = cls._SETUP_CACHE[key]
            if ok:
                return
            if fallback == "skip_if_setup_fails":
                pytest.skip(f"{label} setup failed: {msg}")
            pytest.fail(f"{label} setup failed: {msg}")
        for cmd in setup_cmds:
            r = subprocess.run(cmd, cwd=cls.REPO_DIR, shell=True,
                               capture_output=True, text=True, timeout=300)
            if r.returncode != 0:
                msg = (r.stderr or r.stdout or 'failed').strip()
                cls._SETUP_CACHE[key] = (False, msg)
                if fallback == "skip_if_setup_fails":
                    pytest.skip(f"{label} setup failed: {msg}")
                pytest.fail(f"{label} setup failed: {msg}")
        cls._SETUP_CACHE[key] = (True, 'ok')


    # ── file_path_check (static) ────────────────────────────────────────

    def test_similarity_modules_exist(self):
        """Verify all similarity search modules exist"""
        _p = self._repo_path('src/similarity/faiss_store.py')
        assert os.path.isfile(_p), f'Missing file: src/similarity/faiss_store.py'
        py_compile.compile(_p, doraise=True)
        _p = self._repo_path('src/similarity/pinecone_store.py')
        assert os.path.isfile(_p), f'Missing file: src/similarity/pinecone_store.py'
        py_compile.compile(_p, doraise=True)
        _p = self._repo_path('src/similarity/hybrid.py')
        assert os.path.isfile(_p), f'Missing file: src/similarity/hybrid.py'
        py_compile.compile(_p, doraise=True)

    def test_similarity_test_file_exists(self):
        """Verify test file exists"""
        _p = self._repo_path('tests/test_similarity.py')
        assert os.path.isfile(_p), f'Missing file: tests/test_similarity.py'
        py_compile.compile(_p, doraise=True)

    # ── semantic_check (static) ────────────────────────────────────────

    def test_faiss_store_class_shape(self):
        """Verify FAISSStore class with add and search methods"""
        _p = self._repo_path('src/similarity/faiss_store.py')
        assert os.path.exists(_p), f'Missing: src/similarity/faiss_store.py'
        _contents = self._safe_read(_p)
        _all = _contents if isinstance(_contents, str) else ''
        assert 'class FAISSStore' in _all, 'Missing: class FAISSStore'
        assert 'add' in _all, 'Missing: add'
        assert 'search' in _all, 'Missing: search'
        assert 'faiss' in _all, 'Missing: faiss'
        assert 'dim' in _all, 'Missing: dim'

    def test_hybrid_search_rrf(self):
        """Verify HybridSearch uses Reciprocal Rank Fusion"""
        _p = self._repo_path('src/similarity/hybrid.py')
        assert os.path.exists(_p), f'Missing: src/similarity/hybrid.py'
        _contents = self._safe_read(_p)
        _all = _contents if isinstance(_contents, str) else ''
        assert 'class HybridSearch' in _all, 'Missing: class HybridSearch'
        assert 'search' in _all, 'Missing: search'
        assert 'alpha' in _all, 'Missing: alpha'
        assert 'rank' in _all, 'Missing: rank'
        assert 'rrf' in _all, 'Missing: rrf'
        assert 'reciprocal' in _all, 'Missing: reciprocal'

    def test_pinecone_store_filter_support(self):
        """Verify PineconeStore.query accepts filter parameter"""
        _p = self._repo_path('src/similarity/pinecone_store.py')
        assert os.path.exists(_p), f'Missing: src/similarity/pinecone_store.py'
        _contents = self._safe_read(_p)
        _all = _contents if isinstance(_contents, str) else ''
        assert 'class PineconeStore' in _all, 'Missing: class PineconeStore'
        assert 'query' in _all, 'Missing: query'
        assert 'filter' in _all, 'Missing: filter'
        assert 'upsert' in _all, 'Missing: upsert'
        assert 'metadata' in _all, 'Missing: metadata'

    # ── functional_check ────────────────────────────────────────

    def test_faiss_store_add_and_search(self):
        """Verify FAISSStore add and search work correctly"""
        self._ensure_setup('test_faiss_store_add_and_search', ['pip install faiss-cpu numpy'], 'fail_if_missing')
        result = self._run_cmd('python', args=['-c', "import numpy as np; from src.similarity.faiss_store import FAISSStore; store=FAISSStore(dim=128); vecs=np.random.rand(10,128).astype('float32'); store.add(['text'+str(i) for i in range(10)], vecs); results=store.search(vecs[0], k=3); assert len(results)<=3; print('PASS')"], timeout=120)
        assert result.returncode == 0, (
            f'test_faiss_store_add_and_search failed (exit {result.returncode})\n' + result.stderr[:500]
        )

    def test_scores_normalized_zero_to_one(self):
        """Verify search scores are in [0,1] range"""
        self._ensure_setup('test_scores_normalized_zero_to_one', ['pip install faiss-cpu numpy'], 'fail_if_missing')
        result = self._run_cmd('python', args=['-c', "import numpy as np; from src.similarity.faiss_store import FAISSStore; store=FAISSStore(dim=128); vecs=np.random.rand(10,128).astype('float32'); store.add(['t'+str(i) for i in range(10)], vecs); results=store.search(vecs[0], k=3); assert all(0<=score<=1 for _,score in results); print('PASS')"], timeout=120)
        assert result.returncode == 0, (
            f'test_scores_normalized_zero_to_one failed (exit {result.returncode})\n' + result.stderr[:500]
        )

    def test_empty_store_returns_empty(self):
        """Verify empty index search returns [] not exception"""
        self._ensure_setup('test_empty_store_returns_empty', ['pip install faiss-cpu numpy'], 'fail_if_missing')
        result = self._run_cmd('python', args=['-c', "import numpy as np; from src.similarity.faiss_store import FAISSStore; store=FAISSStore(dim=128); q=np.random.rand(128).astype('float32'); results=store.search(q, k=5); assert results==[]; print('PASS')"], timeout=120)
        assert result.returncode == 0, (
            f'test_empty_store_returns_empty failed (exit {result.returncode})\n' + result.stderr[:500]
        )

    def test_k_larger_than_index(self):
        """Verify k > index size returns all available vectors"""
        self._ensure_setup('test_k_larger_than_index', ['pip install faiss-cpu numpy'], 'fail_if_missing')
        result = self._run_cmd('python', args=['-c', "import numpy as np; from src.similarity.faiss_store import FAISSStore; store=FAISSStore(dim=128); vecs=np.random.rand(3,128).astype('float32'); store.add(['a','b','c'], vecs); results=store.search(vecs[0], k=10); assert len(results)==3; print('PASS')"], timeout=120)
        assert result.returncode == 0, (
            f'test_k_larger_than_index failed (exit {result.returncode})\n' + result.stderr[:500]
        )

    def test_hybrid_alpha_pure_dense(self):
        """Verify HybridSearch alpha=1.0 returns pure dense results"""
        self._ensure_setup('test_hybrid_alpha_pure_dense', ['pip install faiss-cpu numpy rank-bm25 pytest'], 'fail_if_missing')
        result = self._run_cmd('python', args=['-m', 'pytest', 'tests/test_similarity.py', '-v', '-k', 'test_alpha_pure_dense'], timeout=120)
        assert result.returncode == 0, (
            f'test_hybrid_alpha_pure_dense failed (exit {result.returncode})\n' + result.stderr[:500]
        )

    def test_dimension_mismatch_error(self):
        """Verify wrong embedding dimension raises error"""
        self._ensure_setup('test_dimension_mismatch_error', ['pip install faiss-cpu numpy'], 'fail_if_missing')
        result = self._run_cmd('python', args=['-c', "import numpy as np; from src.similarity.faiss_store import FAISSStore; store=FAISSStore(dim=128)\ntry:\n    store.add(['text'], np.random.rand(1,256).astype('float32'))\n    assert False, 'Should have raised'\nexcept (ValueError, RuntimeError):\n    print('PASS')"], timeout=120)
        assert result.returncode == 0, (
            f'test_dimension_mismatch_error failed (exit {result.returncode})\n' + result.stderr[:500]
        )

    def test_full_similarity_suite(self):
        """Run the full similarity search test suite (excluding Pinecone)"""
        self._ensure_setup('test_full_similarity_suite', ['pip install faiss-cpu numpy rank-bm25 pytest'], 'fail_if_missing')
        result = self._run_cmd('python', args=['-m', 'pytest', 'tests/test_similarity.py', '-v', '-k', 'not pinecone', '--tb=short'], timeout=120)
        assert result.returncode == 0, (
            f'test_full_similarity_suite failed (exit {result.returncode})\n' + result.stderr[:500]
        )

