"""
Test for 'llm-evaluation' skill — LLM Evaluation
Validates EvaluationSuite and EvaluationResult in the HELM benchmark framework,
covering exact_match, f1, judge metrics, custom metrics, and edge cases.
"""

import os
import re
import ast
import sys
import pytest


class TestLlmEvaluation:
    """Tests for LLM evaluation suite in the helm repo."""

    REPO_DIR = "/workspace/helm"

    def _read(self, relpath):
        full = os.path.join(self.REPO_DIR, relpath)
        with open(full, "r", errors="ignore") as f:
            return f.read()

    # --- File Path Checks ---

    def test_eval_suite_py_exists(self):
        """Verifies that helm/benchmark/evaluation/eval_suite.py exists."""
        path = os.path.join(
            self.REPO_DIR, "helm", "benchmark", "evaluation", "eval_suite.py"
        )
        assert os.path.exists(path), f"Expected file not found: {path}"

    def test_evaluation_init_py_exists(self):
        """Verifies that helm/benchmark/evaluation/__init__.py exists."""
        path = os.path.join(
            self.REPO_DIR, "helm", "benchmark", "evaluation", "__init__.py"
        )
        assert os.path.exists(path), f"Expected file not found: {path}"

    # --- Semantic Checks ---

    def test_sem_import_evaluation_suite_and_result(self):
        """from helm.benchmark.evaluation.eval_suite import EvaluationSuite, EvaluationResult — importable."""
        old_path = sys.path[:]
        sys.path.insert(0, self.REPO_DIR)
        try:
            from helm.benchmark.evaluation.eval_suite import (
                EvaluationSuite,
                EvaluationResult,
            )

            assert EvaluationSuite is not None
            assert EvaluationResult is not None
        finally:
            sys.path[:] = old_path

    def test_sem_constructor_has_predict_fn_metrics_judge_fn(self):
        """EvaluationSuite constructor has predict_fn, metrics, judge_fn parameters."""
        content = self._read("helm/benchmark/evaluation/eval_suite.py")
        tree = ast.parse(content)
        for node in ast.walk(tree):
            if isinstance(node, ast.ClassDef) and node.name == "EvaluationSuite":
                for item in node.body:
                    if isinstance(item, ast.FunctionDef) and item.name == "__init__":
                        arg_names = [a.arg for a in item.args.args if a.arg != "self"]
                        assert (
                            "predict_fn" in arg_names
                        ), f"predict_fn not in __init__ args: {arg_names}"
                        assert (
                            "metrics" in arg_names
                        ), f"metrics not in __init__ args: {arg_names}"
                        assert (
                            "judge_fn" in arg_names
                        ), f"judge_fn not in __init__ args: {arg_names}"
                        return
        pytest.fail("EvaluationSuite.__init__ not found")

    def test_sem_evaluation_result_attributes(self):
        """EvaluationResult has attributes: scores_by_metric, mean_score_by_metric, overall_score, dataset_size."""
        content = self._read("helm/benchmark/evaluation/eval_suite.py")
        for attr in [
            "scores_by_metric",
            "mean_score_by_metric",
            "overall_score",
            "dataset_size",
        ]:
            assert attr in content, f"Attribute '{attr}' not found in eval_suite.py"

    def test_sem_get_supported_metrics_includes_exact_match_f1(self):
        """EvaluationSuite.get_supported_metrics() includes at least 'exact_match' and 'f1'."""
        content = self._read("helm/benchmark/evaluation/eval_suite.py")
        assert "exact_match" in content, "'exact_match' not found in eval_suite.py"
        assert "f1" in content, "'f1' not found in eval_suite.py"
        assert re.search(
            r"def\s+get_supported_metrics", content
        ), "get_supported_metrics method not found"

    # --- Functional Checks (import) ---

    def test_func_exact_match_perfect_score(self):
        """predict_fn returns 'hello world', reference='hello world' -> exact_match == 1.0."""
        old_path = sys.path[:]
        sys.path.insert(0, self.REPO_DIR)
        try:
            from helm.benchmark.evaluation.eval_suite import EvaluationSuite

            predict_fn = lambda prompt: "hello world"
            suite = EvaluationSuite(predict_fn, ["exact_match"])
            result = suite.evaluate([{"prompt": "q", "reference": "hello world"}])
            assert result.mean_score_by_metric["exact_match"] == 1.0
        finally:
            sys.path[:] = old_path

    def test_func_exact_match_zero_score(self):
        """predict_fn returns 'hello world', reference='different answer' -> exact_match == 0.0."""
        old_path = sys.path[:]
        sys.path.insert(0, self.REPO_DIR)
        try:
            from helm.benchmark.evaluation.eval_suite import EvaluationSuite

            predict_fn = lambda prompt: "hello world"
            suite = EvaluationSuite(predict_fn, ["exact_match"])
            result = suite.evaluate([{"prompt": "q", "reference": "different answer"}])
            assert result.mean_score_by_metric["exact_match"] == 0.0
        finally:
            sys.path[:] = old_path

    def test_func_case_insensitive_exact_match(self):
        """Case-insensitive: predict_fn returns 'Hello World', reference='hello world' -> exact_match == 1.0."""
        old_path = sys.path[:]
        sys.path.insert(0, self.REPO_DIR)
        try:
            from helm.benchmark.evaluation.eval_suite import EvaluationSuite

            predict_fn = lambda prompt: "Hello World"
            suite = EvaluationSuite(predict_fn, ["exact_match"])
            result = suite.evaluate([{"prompt": "q", "reference": "hello world"}])
            assert result.mean_score_by_metric["exact_match"] == 1.0
        finally:
            sys.path[:] = old_path

    def test_func_f1_partial_overlap(self):
        """f1 metric: predict='a b c', reference='a b d' -> f1 ≈ 2/3."""
        old_path = sys.path[:]
        sys.path.insert(0, self.REPO_DIR)
        try:
            from helm.benchmark.evaluation.eval_suite import EvaluationSuite

            f1_suite = EvaluationSuite(lambda p: "a b c", ["f1"])
            r = f1_suite.evaluate([{"prompt": "x", "reference": "a b d"}])
            assert (
                abs(r.mean_score_by_metric["f1"] - 2 / 3) < 0.01
            ), f"Expected f1 ≈ 0.667, got {r.mean_score_by_metric['f1']}"
        finally:
            sys.path[:] = old_path

    def test_func_empty_dataset(self):
        """Empty dataset: evaluate([]).dataset_size == 0."""
        old_path = sys.path[:]
        sys.path.insert(0, self.REPO_DIR)
        try:
            from helm.benchmark.evaluation.eval_suite import EvaluationSuite

            predict_fn = lambda prompt: "hello world"
            suite = EvaluationSuite(predict_fn, ["exact_match"])
            result = suite.evaluate([])
            assert result.dataset_size == 0
        finally:
            sys.path[:] = old_path

    def test_func_judge_fn_called(self):
        """Mock judge_fn is called when 'judge' metric is used."""
        from unittest.mock import Mock

        old_path = sys.path[:]
        sys.path.insert(0, self.REPO_DIR)
        try:
            from helm.benchmark.evaluation.eval_suite import EvaluationSuite

            predict_fn = lambda prompt: "hello world"
            mock_judge = Mock(return_value=0.8)
            judge_suite = EvaluationSuite(predict_fn, ["judge"], judge_fn=mock_judge)
            judge_suite.evaluate([{"prompt": "q", "reference": "r"}])
            assert mock_judge.called, "judge_fn was not called"
        finally:
            sys.path[:] = old_path

    def test_func_judge_without_fn_raises_value_error(self):
        """Using 'judge' metric with judge_fn=None raises ValueError."""
        old_path = sys.path[:]
        sys.path.insert(0, self.REPO_DIR)
        try:
            from helm.benchmark.evaluation.eval_suite import EvaluationSuite

            predict_fn = lambda prompt: "hello world"
            suite = EvaluationSuite(predict_fn, ["judge"], judge_fn=None)
            with pytest.raises(ValueError):
                suite.evaluate([{"prompt": "q", "reference": "r"}])
        finally:
            sys.path[:] = old_path

    def test_func_add_custom_metric(self):
        """suite.add_metric('char_match', ...) adds custom metric to results."""
        old_path = sys.path[:]
        sys.path.insert(0, self.REPO_DIR)
        try:
            from helm.benchmark.evaluation.eval_suite import EvaluationSuite

            predict_fn = lambda prompt: "hello"
            suite = EvaluationSuite(predict_fn, ["exact_match"])
            suite.add_metric("char_match", lambda p, r: float(p == r))
            result = suite.evaluate([{"prompt": "q", "reference": "hello"}])
            assert (
                "char_match" in result.scores_by_metric
            ), f"'char_match' not in scores_by_metric: {list(result.scores_by_metric.keys())}"
        finally:
            sys.path[:] = old_path
