"""
Tests for 'rag-implementation' skill.
Generated from benchmark case definitions for rag-implementation.
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


class TestRagImplementation:
    """Verify the rag-implementation skill output."""

    REPO_DIR = '/workspace/langchain'


    # ── helpers ──────────────────────────────────────────────

    _SETUP_CACHE: dict = {}

    @staticmethod
    def _repo_path(rel: str) -> str:
        return os.path.join(TestRagImplementation.REPO_DIR, rel)

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

    def test_rag_modules_exist(self):
        """Verify all RAG source modules exist"""
        _p = self._repo_path('src/rag/ingestion.py')
        assert os.path.isfile(_p), f'Missing file: src/rag/ingestion.py'
        py_compile.compile(_p, doraise=True)
        _p = self._repo_path('src/rag/retriever.py')
        assert os.path.isfile(_p), f'Missing file: src/rag/retriever.py'
        py_compile.compile(_p, doraise=True)
        _p = self._repo_path('src/rag/pipeline.py')
        assert os.path.isfile(_p), f'Missing file: src/rag/pipeline.py'
        py_compile.compile(_p, doraise=True)

    def test_rag_test_file_exists(self):
        """Verify test file exists"""
        _p = self._repo_path('tests/test_rag.py')
        assert os.path.isfile(_p), f'Missing file: tests/test_rag.py'
        py_compile.compile(_p, doraise=True)

    # ── semantic_check (static) ────────────────────────────────────────

    def test_document_ingester_class(self):
        """Verify DocumentIngester class with ingest and chunk methods"""
        _p = self._repo_path('src/rag/ingestion.py')
        assert os.path.exists(_p), f'Missing: src/rag/ingestion.py'
        _contents = self._safe_read(_p)
        _all = _contents if isinstance(_contents, str) else ''
        assert 'class DocumentIngester' in _all, 'Missing: class DocumentIngester'
        assert 'ingest' in _all, 'Missing: ingest'
        assert 'chunk' in _all, 'Missing: chunk'
        assert 'chunk_size' in _all, 'Missing: chunk_size'
        assert 'overlap' in _all, 'Missing: overlap'

    def test_retriever_class(self):
        """Verify Retriever class with retrieve method returning Documents"""
        _p = self._repo_path('src/rag/retriever.py')
        assert os.path.exists(_p), f'Missing: src/rag/retriever.py'
        _contents = self._safe_read(_p)
        _all = _contents if isinstance(_contents, str) else ''
        assert 'class Retriever' in _all, 'Missing: class Retriever'
        assert 'retrieve' in _all, 'Missing: retrieve'
        assert 'top_k' in _all, 'Missing: top_k'
        assert 'Document' in _all, 'Missing: Document'

    def test_rag_pipeline_uses_state_graph(self):
        """Verify RAGPipeline uses LangGraph StateGraph with retrieve/augment/generate nodes"""
        _p = self._repo_path('src/rag/pipeline.py')
        assert os.path.exists(_p), f'Missing: src/rag/pipeline.py'
        _contents = self._safe_read(_p)
        _all = _contents if isinstance(_contents, str) else ''
        assert 'StateGraph' in _all, 'Missing: StateGraph'
        assert 'RAGPipeline' in _all, 'Missing: RAGPipeline'
        assert 'invoke' in _all, 'Missing: invoke'
        assert 'retrieve' in _all, 'Missing: retrieve'
        assert 'augment' in _all, 'Missing: augment'
        assert 'generate' in _all, 'Missing: generate'

    def test_pipeline_returns_dict_with_answer(self):
        """Verify invoke returns dict with 'answer', 'sources', 'context' keys"""
        _p = self._repo_path('src/rag/pipeline.py')
        assert os.path.exists(_p), f'Missing: src/rag/pipeline.py'
        _contents = self._safe_read(_p)
        _all = _contents if isinstance(_contents, str) else ''
        assert 'answer' in _all, 'Missing: answer'
        assert 'sources' in _all, 'Missing: sources'
        assert 'context' in _all, 'Missing: context'

    # ── functional_check ────────────────────────────────────────

    def test_chunk_produces_overlapping_segments(self):
        """Verify chunk produces overlapping text segments"""
        self._ensure_setup('test_chunk_produces_overlapping_segments', ['pip install langchain langgraph faiss-cpu'], 'fail_if_missing')
        result = self._run_cmd('python', args=['-c', "from src.rag.ingestion import DocumentIngester; d=DocumentIngester(); chunks=d.chunk('a '*200, chunk_size=100, overlap=20); assert isinstance(chunks, list); assert len(chunks)>1; assert all(len(c)<=120 for c in chunks); print('PASS')"], timeout=120)
        assert result.returncode == 0, (
            f'test_chunk_produces_overlapping_segments failed (exit {result.returncode})\n' + result.stderr[:500]
        )

    def test_retrieve_returns_top_k_docs(self):
        """Verify retrieve returns exactly top_k Document objects"""
        self._ensure_setup('test_retrieve_returns_top_k_docs', ['pip install langchain langgraph faiss-cpu'], 'fail_if_missing')
        result = self._run_cmd('python', args=['-m', 'pytest', 'tests/test_rag.py', '-v', '-k', 'test_retrieve_top_k'], timeout=120)
        assert result.returncode == 0, (
            f'test_retrieve_returns_top_k_docs failed (exit {result.returncode})\n' + result.stderr[:500]
        )

    def test_pipeline_invoke_with_mock_llm(self):
        """Verify RAGPipeline.invoke returns dict with answer and sources using mock LLM"""
        self._ensure_setup('test_pipeline_invoke_with_mock_llm', ['pip install langchain langgraph faiss-cpu pytest'], 'fail_if_missing')
        result = self._run_cmd('python', args=['-m', 'pytest', 'tests/test_rag.py', '-v', '-k', 'test_pipeline_invoke'], timeout=120)
        assert result.returncode == 0, (
            f'test_pipeline_invoke_with_mock_llm failed (exit {result.returncode})\n' + result.stderr[:500]
        )

    def test_empty_ingestion(self):
        """Verify ingest([]) succeeds without error"""
        self._ensure_setup('test_empty_ingestion', ['pip install langchain langgraph faiss-cpu'], 'fail_if_missing')
        result = self._run_cmd('python', args=['-c', "from src.rag.ingestion import DocumentIngester; d=DocumentIngester(); d.ingest([]); print('PASS')"], timeout=120)
        assert result.returncode == 0, (
            f'test_empty_ingestion failed (exit {result.returncode})\n' + result.stderr[:500]
        )

    def test_no_context_uncertainty_response(self):
        """Verify pipeline with no context returns uncertainty phrase"""
        self._ensure_setup('test_no_context_uncertainty_response', ['pip install langchain langgraph faiss-cpu pytest'], 'fail_if_missing')
        result = self._run_cmd('python', args=['-m', 'pytest', 'tests/test_rag.py', '-v', '-k', 'test_no_context'], timeout=120)
        assert result.returncode == 0, (
            f'test_no_context_uncertainty_response failed (exit {result.returncode})\n' + result.stderr[:500]
        )

    def test_invalid_document_raises(self):
        """Verify ingest with None text raises ValueError"""
        self._ensure_setup('test_invalid_document_raises', ['pip install langchain langgraph faiss-cpu'], 'fail_if_missing')
        result = self._run_cmd('python', args=['-c', "from src.rag.ingestion import DocumentIngester; d=DocumentIngester()\ntry:\n    d.ingest([None])\n    assert False, 'Should have raised'\nexcept (ValueError, TypeError):\n    print('PASS')"], timeout=120)
        assert result.returncode == 0, (
            f'test_invalid_document_raises failed (exit {result.returncode})\n' + result.stderr[:500]
        )

