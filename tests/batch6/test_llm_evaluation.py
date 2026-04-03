"""
Tests for 'llm-evaluation' skill.
Generated from benchmark case definitions for llm-evaluation.
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


class TestLlmEvaluation:
    """Verify the llm-evaluation skill output."""

    REPO_DIR = '/workspace/helm'


    # ── helpers ──────────────────────────────────────────────

    _SETUP_CACHE: dict = {}

    @staticmethod
    def _repo_path(rel: str) -> str:
        return os.path.join(TestLlmEvaluation.REPO_DIR, rel)

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

    def test_metrics_module_exists(self):
        """Verify metrics.py exists"""
        _p = self._repo_path('src/evaluation/metrics.py')
        assert os.path.isfile(_p), f'Missing file: src/evaluation/metrics.py'
        py_compile.compile(_p, doraise=True)

    def test_llm_judge_module_exists(self):
        """Verify llm_judge.py exists"""
        _p = self._repo_path('src/evaluation/llm_judge.py')
        assert os.path.isfile(_p), f'Missing file: src/evaluation/llm_judge.py'
        py_compile.compile(_p, doraise=True)

    def test_suite_module_exists(self):
        """Verify suite.py exists"""
        _p = self._repo_path('src/evaluation/suite.py')
        assert os.path.isfile(_p), f'Missing file: src/evaluation/suite.py'
        py_compile.compile(_p, doraise=True)

    # ── semantic_check (static) ────────────────────────────────────────

    def test_metrics_class_methods(self):
        """Verify EvaluationMetrics has compute_bleu, compute_rouge, semantic_similarity"""
        _p = self._repo_path('src/evaluation/metrics.py')
        assert os.path.exists(_p), f'Missing: src/evaluation/metrics.py'
        _contents = self._safe_read(_p)
        _all = _contents if isinstance(_contents, str) else ''
        assert 'compute_bleu' in _all, 'Missing: compute_bleu'
        assert 'compute_rouge' in _all, 'Missing: compute_rouge'
        assert 'semantic_similarity' in _all, 'Missing: semantic_similarity'

    def test_judge_score_method(self):
        """Verify LLMJudge has score method with structured output"""
        _p = self._repo_path('src/evaluation/llm_judge.py')
        assert os.path.exists(_p), f'Missing: src/evaluation/llm_judge.py'
        _contents = self._safe_read(_p)
        _all = _contents if isinstance(_contents, str) else ''
        assert 'score' in _all, 'Missing: score'
        assert 'reasoning' in _all, 'Missing: reasoning'

    def test_suite_returns_dataframe(self):
        """Verify EvaluationSuite.run returns DataFrame"""
        _p = self._repo_path('src/evaluation/suite.py')
        assert os.path.exists(_p), f'Missing: src/evaluation/suite.py'
        _contents = self._safe_read(_p)
        _all = _contents if isinstance(_contents, str) else ''
        assert 'DataFrame' in _all, 'Missing: DataFrame'
        assert 'run' in _all, 'Missing: run'

    # ── functional_check ────────────────────────────────────────

    def test_bleu_perfect_match(self):
        """Verify compute_bleu returns 1.0 for identical texts"""
        self._ensure_setup('test_bleu_perfect_match', ['pip install sacrebleu rouge-score'], 'fail_if_missing')
        result = self._run_cmd('python', args=['-c', "from src.evaluation.metrics import EvaluationMetrics; m=EvaluationMetrics(); assert m.compute_bleu('hello world','hello world')==1.0; print('PASS')"], timeout=120)
        assert result.returncode == 0, (
            f'test_bleu_perfect_match failed (exit {result.returncode})\n' + result.stderr[:500]
        )
        assert 'PASS' in (result.stdout + result.stderr), 'Expected PASS in output'

    def test_bleu_empty_hypothesis(self):
        """Verify compute_bleu returns 0.0 for empty hypothesis"""
        self._ensure_setup('test_bleu_empty_hypothesis', ['pip install sacrebleu'], 'fail_if_missing')
        result = self._run_cmd('python', args=['-c', "from src.evaluation.metrics import EvaluationMetrics; m=EvaluationMetrics(); score=m.compute_bleu('hello world',''); assert score==0.0, f'Expected 0.0 got {score}'; print('PASS')"], timeout=120)
        assert result.returncode == 0, (
            f'test_bleu_empty_hypothesis failed (exit {result.returncode})\n' + result.stderr[:500]
        )
        assert 'PASS' in (result.stdout + result.stderr), 'Expected PASS in output'

    def test_rouge_perfect_match(self):
        """Verify compute_rouge returns F1=1.0 for identical texts"""
        self._ensure_setup('test_rouge_perfect_match', ['pip install rouge-score'], 'fail_if_missing')
        result = self._run_cmd('python', args=['-c', "from src.evaluation.metrics import EvaluationMetrics; m=EvaluationMetrics(); r=m.compute_rouge('hello world','hello world','rouge1'); assert r['f']==1.0 or r>=0.99; print('PASS')"], timeout=120)
        assert result.returncode == 0, (
            f'test_rouge_perfect_match failed (exit {result.returncode})\n' + result.stderr[:500]
        )
        assert 'PASS' in (result.stdout + result.stderr), 'Expected PASS in output'

    def test_bleu_range_check(self):
        """Verify BLEU score is in [0,1] for partial overlap"""
        self._ensure_setup('test_bleu_range_check', ['pip install sacrebleu'], 'fail_if_missing')
        result = self._run_cmd('python', args=['-c', "from src.evaluation.metrics import EvaluationMetrics; m=EvaluationMetrics(); score=m.compute_bleu('the cat sat on the mat','the cat was on the mat'); assert 0.0<=score<=1.0, f'Out of range: {score}'; print('PASS')"], timeout=120)
        assert result.returncode == 0, (
            f'test_bleu_range_check failed (exit {result.returncode})\n' + result.stderr[:500]
        )
        assert 'PASS' in (result.stdout + result.stderr), 'Expected PASS in output'

    def test_pytest_evaluation(self):
        """Run pytest for evaluation tests excluding LLM judge"""
        self._ensure_setup('test_pytest_evaluation', ['pip install sacrebleu rouge-score pandas pytest'], 'fail_if_missing')
        result = self._run_cmd('python', args=['-m', 'pytest', 'tests/test_evaluation.py', '-v', '-k', 'not llm_judge', '--tb=short'], timeout=120)
        assert result.returncode == 0, (
            f'test_pytest_evaluation failed (exit {result.returncode})\n' + result.stderr[:500]
        )

    def test_judge_score_type(self):
        """Verify LLMJudge.score returns dict with int score and str reasoning (mocked)"""
        self._ensure_setup('test_judge_score_type', ['pip install pytest'], 'fail_if_missing')
        result = self._run_cmd('python', args=['-c', 'from unittest.mock import MagicMock; from src.evaluation.llm_judge import LLMJudge; mock_llm=MagicMock(); mock_llm.invoke.return_value=MagicMock(content=\'{"score":8,"reasoning":"Good answer"}\'); judge=LLMJudge(llm=mock_llm); result=judge.score(\'q\',\'ref\',\'cand\'); assert isinstance(result[\'score\'],int) and 1<=result[\'score\']<=10; assert isinstance(result[\'reasoning\'],str); print(\'PASS\')'], timeout=120)
        assert result.returncode == 0, (
            f'test_judge_score_type failed (exit {result.returncode})\n' + result.stderr[:500]
        )
        assert 'PASS' in (result.stdout + result.stderr), 'Expected PASS in output'

