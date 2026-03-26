"""
Test for 'llm-evaluation' skill — LLM Evaluation
Validates that the Agent created an LLM evaluation demo for HELM with multiple
scenarios, configurable metrics, and summary reporting.
"""

import os
import re
import subprocess


class TestLlmEvaluation:
    """Verify LLM evaluation demo script for HELM."""

    REPO_DIR = "/workspace/helm"

    def _read(self, *parts):
        fpath = os.path.join(self.REPO_DIR, *parts)
        assert os.path.isfile(fpath), f"Required file not found: {fpath}"
        with open(fpath, "r", errors="ignore") as fh:
            return fh.read()

    # ------------------------------------------------------------------
    # L1: File existence and syntax
    # ------------------------------------------------------------------

    def test_demo_file_exists(self):
        """examples/llm_eval_demo.py must exist."""
        assert os.path.isfile(
            os.path.join(self.REPO_DIR, "examples", "llm_eval_demo.py")
        )

    def test_demo_compiles(self):
        """llm_eval_demo.py must be syntactically valid Python."""
        result = subprocess.run(
            ["python", "-m", "py_compile", "examples/llm_eval_demo.py"],
            cwd=self.REPO_DIR,
            capture_output=True,
            text=True,
            timeout=30,
        )
        assert result.returncode == 0, f"Syntax error:\n{result.stderr}"

    def test_has_main_entry_point(self):
        """Script must have a __main__ entry point."""
        content = self._read("examples", "llm_eval_demo.py")
        assert re.search(r'if\s+__name__\s*==\s*["\']__main__["\']', content)

    # ------------------------------------------------------------------
    # L1: Evaluation scenarios
    # ------------------------------------------------------------------

    def test_defines_multiple_scenario_types(self):
        """Script must define multiple evaluation scenario types."""
        content = self._read("examples", "llm_eval_demo.py")
        scenario_types = [
            r"question.*answer",
            r"summariz",
            r"classif",
            r"translation",
            r"generation",
            r"scenario",
        ]
        matches = sum(1 for p in scenario_types if re.search(p, content, re.IGNORECASE))
        assert matches >= 2, (
            f"Only {matches} scenario type(s) referenced — "
            "need at least 2 (e.g., QA, summarization, classification)"
        )

    def test_scenarios_have_inputs_and_expected(self):
        """Each scenario must specify inputs and expected outputs."""
        content = self._read("examples", "llm_eval_demo.py")
        input_patterns = [r"input", r"prompt", r"question", r"text"]
        output_patterns = [r"expected", r"reference", r"ground_truth", r"answer"]
        has_input = any(re.search(p, content, re.IGNORECASE) for p in input_patterns)
        has_expected = any(
            re.search(p, content, re.IGNORECASE) for p in output_patterns
        )
        assert (
            has_input and has_expected
        ), f"Scenarios missing input (found={has_input}) or expected output (found={has_expected})"

    # ------------------------------------------------------------------
    # L1: Metrics
    # ------------------------------------------------------------------

    def test_implements_multiple_metrics(self):
        """Script must implement at least two evaluation metrics."""
        content = self._read("examples", "llm_eval_demo.py")
        metric_patterns = [
            r"exact.match",
            r"f1",
            r"bleu",
            r"rouge",
            r"similarity",
            r"format.*compliance",
            r"accuracy",
            r"precision",
            r"recall",
        ]
        matches = sum(
            1 for p in metric_patterns if re.search(p, content, re.IGNORECASE)
        )
        assert matches >= 2, f"Only {matches} metric(s) found — need at least 2"

    def test_metrics_produce_scores(self):
        """Metrics must produce numeric scores."""
        content = self._read("examples", "llm_eval_demo.py")
        patterns = [
            r"score",
            r"result.*\d|result.*float",
            r"metric.*value",
            r"return.*float",
        ]
        assert any(
            re.search(p, content, re.IGNORECASE) for p in patterns
        ), "Metrics do not appear to produce numeric scores"

    # ------------------------------------------------------------------
    # L1: Configuration
    # ------------------------------------------------------------------

    def test_supports_config_loading(self):
        """Script must support loading scenarios from structured config."""
        content = self._read("examples", "llm_eval_demo.py")
        patterns = [r"json", r"yaml", r"config", r"load.*scenario", r"argparse"]
        assert any(
            re.search(p, content, re.IGNORECASE) for p in patterns
        ), "Script does not support configuration loading"

    def test_configurable_thresholds(self):
        """Script must support configurable pass/fail thresholds."""
        content = self._read("examples", "llm_eval_demo.py")
        patterns = [r"threshold", r"pass.*score", r"min.*score", r"cutoff", r"passing"]
        assert any(
            re.search(p, content, re.IGNORECASE) for p in patterns
        ), "Script does not support configurable thresholds"

    # ------------------------------------------------------------------
    # L2: Result reporting
    # ------------------------------------------------------------------

    def test_generates_per_scenario_results(self):
        """Report must include per-scenario scores."""
        content = self._read("examples", "llm_eval_demo.py")
        patterns = [
            r"per.scenario",
            r"scenario.*score",
            r"result.*scenario",
            r"for.*scenario.*in",
            r"scenario.*result",
        ]
        assert any(
            re.search(p, content, re.IGNORECASE) for p in patterns
        ), "Script does not generate per-scenario results"

    def test_generates_aggregate_score(self):
        """Report must include an aggregate/overall score."""
        content = self._read("examples", "llm_eval_demo.py")
        patterns = [
            r"aggregate",
            r"overall",
            r"total.*score",
            r"average.*score",
            r"mean.*score",
            r"summary",
        ]
        assert any(
            re.search(p, content, re.IGNORECASE) for p in patterns
        ), "Script does not generate an aggregate score"

    def test_shows_pass_fail_status(self):
        """Report must display pass/fail status per scenario."""
        content = self._read("examples", "llm_eval_demo.py")
        patterns = [r"pass", r"fail", r"PASS", r"FAIL", r"passed", r"failed", r"status"]
        assert any(
            re.search(p, content) for p in patterns
        ), "Report does not show pass/fail status"

    def test_uses_model_interface(self):
        """Script must use a model interface (real or mock) to evaluate."""
        content = self._read("examples", "llm_eval_demo.py")
        patterns = [
            r"model",
            r"llm",
            r"generate",
            r"predict",
            r"mock",
            r"Mock",
            r"invoke",
            r"completion",
        ]
        assert any(
            re.search(p, content, re.IGNORECASE) for p in patterns
        ), "Script does not use a model interface"

    def test_metric_weights_configurable(self):
        """Metric weights should be configurable for aggregate scoring."""
        content = self._read("examples", "llm_eval_demo.py")
        patterns = [r"weight", r"weighted", r"importance"]
        has_weights = any(re.search(p, content, re.IGNORECASE) for p in patterns)
        # Weights are optional but expected per the task spec
        if not has_weights:
            # Check for equal weighting (average)
            assert re.search(
                r"average|mean|sum.*len", content, re.IGNORECASE
            ), "No explicit weighting or averaging found for aggregate scoring"
