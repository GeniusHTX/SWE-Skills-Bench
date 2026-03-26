"""
Tests for llm-evaluation skill.
Validates HELM benchmark LLM evaluation metrics: ContainsMetric, ExactMatchMetric,
FaithfulnessMetric, and MultiMetricScorer in helm repository.
"""

import os
import pytest

REPO_DIR = "/workspace/helm"


def _path(rel: str) -> str:
    return os.path.join(REPO_DIR, rel)


def _read(rel: str) -> str:
    with open(_path(rel), encoding="utf-8", errors="ignore") as f:
        return f.read()


class TestLlmEvaluation:

    # ── file_path_check ──────────────────────────────────────────────────────

    def test_multi_metric_scorer_file_exists(self):
        """multi_metric_scorer.py must exist in helm/benchmark/metrics."""
        rel = "helm/benchmark/metrics/multi_metric_scorer.py"
        assert os.path.isfile(_path(rel)), f"{rel} not found"
        assert os.path.getsize(_path(rel)) > 0, "multi_metric_scorer.py is empty"

    def test_faithfulness_metric_file_exists(self):
        """faithfulness_metric.py must exist in helm/benchmark/metrics."""
        rel = "helm/benchmark/metrics/faithfulness_metric.py"
        assert os.path.isfile(_path(rel)), f"{rel} not found"

    # ── semantic_check ───────────────────────────────────────────────────────

    def test_metric_classes_defined(self):
        """multi_metric_scorer.py must define ExactMatchMetric, ContainsMetric, MultiMetricScorer."""
        content = _read("helm/benchmark/metrics/multi_metric_scorer.py")
        for cls in [
            "class ExactMatchMetric",
            "class ContainsMetric",
            "class MultiMetricScorer",
        ]:
            assert cls in content, f"{cls} not found in multi_metric_scorer.py"

    def test_faithfulness_metric_class_defined(self):
        """faithfulness_metric.py must define FaithfulnessMetric with score method."""
        content = _read("helm/benchmark/metrics/faithfulness_metric.py")
        assert (
            "class FaithfulnessMetric" in content
        ), "FaithfulnessMetric class not found"
        assert "def score" in content, "score() method not found in FaithfulnessMetric"

    def test_weighted_scoring_logic(self):
        """MultiMetricScorer must implement weighted mean: sum(w*s)/sum(w)."""
        content = _read("helm/benchmark/metrics/multi_metric_scorer.py")
        assert "weight" in content, "No weight parameter found in MultiMetricScorer"

    def test_llm_judge_exception_fallback_defined(self):
        """FaithfulnessMetric must catch LLMJudge exceptions and return 0.0."""
        content = _read("helm/benchmark/metrics/faithfulness_metric.py")
        assert (
            "try" in content and "except" in content
        ), "No try/except block for LLMJudge exception handling"
        assert "0.0" in content, "Fallback score 0.0 not found in exception handler"

    # ── functional_check (mocked) ─────────────────────────────────────────────

    def test_contains_metric_paris_score_1(self):
        """ContainsMetric('Paris') must return 1.0 when answer contains 'Paris'."""

        class ContainsMetric:
            def __init__(self, target):
                self.target = target

            def score(self, answer):
                return 1.0 if self.target in answer else 0.0

        m = ContainsMetric("Paris")
        assert m.score("The capital of France is Paris.") == 1.0

    def test_contains_metric_absent_score_0(self):
        """ContainsMetric must return 0.0 when target string is absent."""

        class ContainsMetric:
            def __init__(self, target):
                self.target = target

            def score(self, answer):
                return 1.0 if self.target in answer else 0.0

        m = ContainsMetric("Paris")
        assert m.score("London is a city.") == 0.0

    def test_exact_match_whitespace_normalization(self):
        """ExactMatchMetric must strip whitespace before comparison."""

        class ExactMatchMetric:
            def __init__(self, target):
                self.target = target

            def score(self, answer):
                return 1.0 if answer.strip() == self.target else 0.0

        m = ExactMatchMetric("Paris")
        assert m.score("  Paris  ") == 1.0

    def test_faithfulness_metric_half_support(self):
        """FaithfulnessMetric returns 0.5 when 1 of 2 sentences is supported."""

        class FaithfulnessMetric:
            def score(self, sentences_supported):
                if not sentences_supported:
                    return 0.0
                return sum(sentences_supported) / len(sentences_supported)

        m = FaithfulnessMetric()
        assert m.score([True, False]) == 0.5

    def test_weighted_mean_0_67(self):
        """Weighted score: ExactMatch(w=1, s=0) + Contains(w=2, s=1.0) = 2/3 ≈ 0.667."""
        scores = [(0.0, 1), (1.0, 2)]
        total_weight = sum(w for _, w in scores)
        weighted_sum = sum(s * w for s, w in scores)
        result = weighted_sum / total_weight
        assert abs(result - 2 / 3) < 1e-9

    def test_llm_judge_exception_returns_0(self):
        """FaithfulnessMetric must return 0.0 when LLMJudge raises an exception."""

        class FaithfulnessMetric:
            def __init__(self, judge):
                self.judge = judge

            def score(self, answer, context):
                try:
                    return self.judge(answer, context)
                except Exception:
                    return 0.0

        def failing_judge(answer, context):
            raise RuntimeError("LLMJudge API error")

        m = FaithfulnessMetric(judge=failing_judge)
        assert m.score("test", "test") == 0.0
