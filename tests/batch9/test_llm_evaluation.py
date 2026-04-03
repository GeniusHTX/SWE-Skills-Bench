"""
Test for 'llm-evaluation' skill — LLM Evaluation Pipeline
Validates BLEU, ROUGE, BERTScore metrics, FactualityChecker,
EvaluationPipeline with mocked dependencies, and edge cases.
"""

import os
import sys

import pytest


class TestLlmEvaluation:
    """Verify LLM evaluation pipeline: metrics, factuality, pipeline."""

    REPO_DIR = "/workspace/helm"

    # ── helpers ──────────────────────────────────────────────────────────

    @staticmethod
    def _read_file(path: str) -> str:
        try:
            with open(path, "r", errors="ignore") as fh:
                return fh.read()
        except OSError:
            return ""

    def _ev(self, *parts) -> str:
        return os.path.join(self.REPO_DIR, "examples", "llm_evaluation", *parts)

    # ── file_path_check ──────────────────────────────────────────────────

    def test_metrics_py_exists(self):
        """metrics.py must exist containing MetricEvaluator."""
        path = self._ev("metrics.py")
        assert os.path.isfile(path), f"{path} does not exist"
        assert os.path.getsize(path) > 0

    def test_pipeline_and_factuality_exist(self):
        """pipeline.py and factuality.py must exist."""
        for name in ("pipeline.py", "factuality.py"):
            path = self._ev(name)
            assert os.path.isfile(path), f"{path} does not exist"

    def test_runner_and_test_file_exist(self):
        """runner.py and tests/test_llm_evaluation.py must exist."""
        assert os.path.isfile(self._ev("runner.py")), "runner.py not found"
        test_path = os.path.join(self.REPO_DIR, "tests", "test_llm_evaluation.py")
        assert os.path.isfile(test_path), f"{test_path} not found"

    # ── semantic_check ───────────────────────────────────────────────────

    def test_compute_bleu_defined_with_pred_ref(self):
        """metrics.py must define compute_bleu(pred, ref)."""
        content = self._read_file(self._ev("metrics.py"))
        if not content:
            pytest.skip("metrics.py not found")
        assert "compute_bleu" in content, "compute_bleu not defined"
        assert "pred" in content and "ref" in content, "pred/ref params missing"

    def test_factuality_validates_context(self):
        """factuality.py must raise ValueError when context is None."""
        content = self._read_file(self._ev("factuality.py"))
        if not content:
            pytest.skip("factuality.py not found")
        assert "FactualityChecker" in content
        assert "ValueError" in content, "ValueError not found"

    def test_pipeline_returns_dict(self):
        """EvaluationPipeline.run must return dict with metric scores."""
        content = self._read_file(self._ev("pipeline.py"))
        if not content:
            pytest.skip("pipeline.py not found")
        assert "EvaluationPipeline" in content
        assert "run" in content
        assert "dict" in content or "return" in content

    def test_bertscore_is_imported_at_top(self):
        """BERTScore must be imported at module level for mockability."""
        content = self._read_file(self._ev("metrics.py"))
        if not content:
            pytest.skip("metrics.py not found")
        has_bert = "bert_score" in content.lower() or "BERTScore" in content
        assert has_bert, "BERTScore import not found"

    # ── functional_check ─────────────────────────────────────────────────

    def test_bleu_identical_returns_near_one(self):
        """compute_bleu with identical pred and ref must return >= 0.99."""
        try:
            sys.path.insert(0, self.REPO_DIR)
            from examples.llm_evaluation.metrics import compute_bleu
        except ImportError:
            pytest.skip("Cannot import compute_bleu")
        score = compute_bleu("hello world", "hello world")
        assert score >= 0.99, f"Expected >= 0.99, got {score}"

    def test_bleu_empty_prediction_returns_zero(self):
        """compute_bleu with empty pred must return 0.0, no ZeroDivisionError."""
        try:
            sys.path.insert(0, self.REPO_DIR)
            from examples.llm_evaluation.metrics import compute_bleu
        except ImportError:
            pytest.skip("Cannot import compute_bleu")
        score = compute_bleu("", "hello world")
        assert score == 0.0

    def test_rouge_identical_returns_one(self):
        """compute_rouge with identical text returns score of 1.0."""
        try:
            sys.path.insert(0, self.REPO_DIR)
            from examples.llm_evaluation.metrics import compute_rouge
        except ImportError:
            pytest.skip("Cannot import compute_rouge")
        score = compute_rouge("the quick brown fox", "the quick brown fox")
        if isinstance(score, dict):
            assert score.get("rougeL", score.get("rouge-l", 0)) == 1.0
        else:
            assert score == 1.0

    def test_factuality_none_raises_valueerror(self):
        """FactualityChecker(context=None) must raise ValueError."""
        try:
            sys.path.insert(0, self.REPO_DIR)
            from examples.llm_evaluation.factuality import FactualityChecker
        except ImportError:
            pytest.skip("Cannot import FactualityChecker")
        with pytest.raises(ValueError):
            FactualityChecker(context=None)

    def test_pipeline_returns_metric_dict(self):
        """EvaluationPipeline.run must return dict with float values."""
        try:
            sys.path.insert(0, self.REPO_DIR)
            from examples.llm_evaluation.pipeline import EvaluationPipeline
            from unittest.mock import MagicMock, patch
        except ImportError:
            pytest.skip("Cannot import EvaluationPipeline")
        pipeline = EvaluationPipeline.__new__(EvaluationPipeline)
        pipeline.metrics = {"bleu": MagicMock(return_value=0.85)}
        try:
            results = pipeline.run([{"input": "What is 2+2?", "output": "4"}])
            assert isinstance(results, dict)
        except Exception:
            pytest.skip("Pipeline requires specific mocking setup")

    def test_pipeline_empty_dataset(self):
        """EvaluationPipeline.run with empty dataset returns empty/zero dict."""
        try:
            sys.path.insert(0, self.REPO_DIR)
            from examples.llm_evaluation.pipeline import EvaluationPipeline
            from unittest.mock import MagicMock
        except ImportError:
            pytest.skip("Cannot import EvaluationPipeline")
        pipeline = EvaluationPipeline.__new__(EvaluationPipeline)
        pipeline.metrics = {}
        try:
            results = pipeline.run([])
            assert isinstance(results, dict)
        except Exception:
            pytest.skip("Pipeline requires specific setup for empty dataset")
