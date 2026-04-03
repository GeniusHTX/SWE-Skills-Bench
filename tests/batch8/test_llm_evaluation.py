"""
Test for 'llm-evaluation' skill — LLM Quality Evaluator
Validates that the Agent created a Python module for evaluating LLM outputs
with judge functions, pass counts, error handling, and per-sample results.
"""

import os
import re
import sys

import pytest


class TestLlmEvaluation:
    """Verify LLM evaluation module implementation."""

    REPO_DIR = "/workspace/helm"

    @staticmethod
    def _read(path: str) -> str:
        try:
            with open(path, "r", errors="ignore") as fh:
                return fh.read()
        except OSError:
            return ""

    # ── file_path_check ─────────────────────────────────────────────

    def test_llm_evaluation_package_exists(self):
        """Verify __init__.py and judge.py exist under src/llm_evaluation/."""
        for rel in ("src/llm_evaluation/__init__.py", "src/llm_evaluation/judge.py"):
            path = os.path.join(self.REPO_DIR, rel)
            assert os.path.isfile(path), f"Missing: {rel}"

    def test_evaluator_suite_models_exist(self):
        """Verify evaluator.py, suite.py, and models.py exist."""
        for rel in ("src/llm_evaluation/evaluator.py", "src/llm_evaluation/suite.py",
                     "src/llm_evaluation/models.py"):
            path = os.path.join(self.REPO_DIR, rel)
            assert os.path.isfile(path), f"Missing: {rel}"

    def test_classes_importable(self):
        """LLMJudge, QualityEvaluator, EvaluationSuite are importable."""
        if not os.path.isdir(self.REPO_DIR):
            pytest.skip("Repo dir does not exist")
        sys.path.insert(0, os.path.join(self.REPO_DIR, "src"))
        try:
            from llm_evaluation.judge import LLMJudge  # noqa: F401
            from llm_evaluation.evaluator import QualityEvaluator  # noqa: F401
            from llm_evaluation.suite import EvaluationSuite  # noqa: F401
        except ImportError:
            pytest.skip("llm_evaluation not importable")
        finally:
            sys.path.pop(0)

    # ── semantic_check ──────────────────────────────────────────────

    def test_judgement_result_and_evaluation_report_models(self):
        """Verify models.py defines JudgementResult, EvaluationReport, avg_score, per_sample_results."""
        content = self._read(os.path.join(self.REPO_DIR, "src/llm_evaluation/models.py"))
        assert content, "models.py is empty or unreadable"
        for field in ("JudgementResult", "EvaluationReport", "avg_score", "per_sample_results"):
            assert field in content, f"'{field}' not found in models.py"

    def test_pass_count_threshold_configurable(self):
        """Verify evaluator.py implements pass_count with configurable threshold."""
        content = self._read(os.path.join(self.REPO_DIR, "src/llm_evaluation/evaluator.py"))
        assert content, "evaluator.py is empty or unreadable"
        assert "pass_count" in content, "'pass_count' not found"
        assert "threshold" in content, "'threshold' not found"

    def test_exception_handling_in_evaluator(self):
        """Verify evaluator.py handles judge_fn exceptions gracefully."""
        content = self._read(os.path.join(self.REPO_DIR, "src/llm_evaluation/evaluator.py"))
        assert content, "evaluator.py is empty or unreadable"
        found = any(kw in content for kw in ("try:", "except", "Exception"))
        assert found, "No exception handling found in evaluator.py"

    # ── functional_check (import) ───────────────────────────────────

    def _import(self, dotpath: str):
        if not os.path.isdir(self.REPO_DIR):
            pytest.skip("Repo dir does not exist")
        sys.path.insert(0, os.path.join(self.REPO_DIR, "src"))
        try:
            return __import__(dotpath, fromlist=[""])
        except ImportError:
            pytest.skip(f"{dotpath} not importable")
        finally:
            sys.path.pop(0)

    def test_single_sample_avg_score(self):
        """Single sample with mock_judge returning 0.8 produces avg_score=0.8."""
        mod = self._import("llm_evaluation.evaluator")
        mock_judge = lambda q, a, r: 0.8
        report = mod.QualityEvaluator().evaluate(
            [{"q": "hi", "a": "hello", "rubric": {}}], mock_judge)
        assert report.avg_score == 0.8

    def test_empty_dataset_returns_zeros(self):
        """evaluate([]) returns avg_score=0.0 and pass_count=0."""
        mod = self._import("llm_evaluation.evaluator")
        report = mod.QualityEvaluator().evaluate([], lambda q, a, r: 0.5)
        assert report.avg_score == 0.0
        assert report.pass_count == 0

    def test_pass_count_at_threshold(self):
        """Scores [0.5, 0.8, 0.9] with threshold=0.7 produce pass_count=2."""
        mod = self._import("llm_evaluation.evaluator")
        scores = [0.5, 0.8, 0.9]
        idx = {"i": 0}

        def judge(q, a, r):
            s = scores[idx["i"]]
            idx["i"] += 1
            return s

        report = mod.QualityEvaluator(threshold=0.7).evaluate(
            [{"q": "q", "a": "a", "rubric": {}} for _ in scores], judge)
        assert report.pass_count == 2

    def test_failing_judge_marks_sample_score_zero(self):
        """When judge_fn raises, the sample is scored 0.0."""
        mod = self._import("llm_evaluation.evaluator")

        def bad_judge(q, a, r):
            raise ValueError("API error")

        report = mod.QualityEvaluator().evaluate(
            [{"q": "q", "a": "a", "rubric": {}}], bad_judge)
        assert report.per_sample_results[0].score == 0.0

    def test_per_sample_results_count_matches_dataset(self):
        """len(report.per_sample_results) equals number of dataset samples."""
        mod = self._import("llm_evaluation.evaluator")
        dataset = [{"q": str(i), "a": "a", "rubric": {}} for i in range(5)]
        report = mod.QualityEvaluator().evaluate(dataset, lambda q, a, r: 1.0)
        assert len(report.per_sample_results) == 5
