"""
Test for 'prompt-engineering-patterns' skill — Prompt Engineering Patterns
Validates that the Agent created a prompt evaluation runner for LangChain
with configurable test cases, automated scoring metrics, and summary reporting.
"""

import os
import re
import subprocess

import pytest

from _dependency_utils import ensure_python_dependencies


@pytest.fixture(scope="module", autouse=True)
def _ensure_repo_dependencies():
    ensure_python_dependencies(TestPromptEngineeringPatterns.REPO_DIR)


class TestPromptEngineeringPatterns:
    """Verify prompt evaluation runner for LangChain."""

    REPO_DIR = "/workspace/langchain"

    def _read(self, *parts):
        fpath = os.path.join(self.REPO_DIR, *parts)
        assert os.path.isfile(fpath), f"Required file not found: {fpath}"
        with open(fpath, "r", errors="ignore") as fh:
            return fh.read()

    # ------------------------------------------------------------------
    # L1: File existence and syntax
    # ------------------------------------------------------------------

    def test_script_exists(self):
        """scripts/run_prompt_eval.py must exist."""
        fpath = os.path.join(self.REPO_DIR, "scripts", "run_prompt_eval.py")
        assert os.path.isfile(fpath), "scripts/run_prompt_eval.py not found"

    def test_script_compiles(self):
        """run_prompt_eval.py must be syntactically valid Python."""
        result = subprocess.run(
            ["python", "-m", "py_compile", "scripts/run_prompt_eval.py"],
            cwd=self.REPO_DIR,
            capture_output=True,
            text=True,
            timeout=30,
        )
        assert result.returncode == 0, f"Syntax error:\n{result.stderr}"

    def test_has_main_entry_point(self):
        """Script must have a __main__ entry point."""
        content = self._read("scripts", "run_prompt_eval.py")
        assert re.search(
            r'if\s+__name__\s*==\s*["\']__main__["\']', content
        ), "Missing __main__ entry point"

    # ------------------------------------------------------------------
    # L1: Evaluation framework structure
    # ------------------------------------------------------------------

    def test_accepts_prompt_templates(self):
        """Script must accept prompt templates as input."""
        content = self._read("scripts", "run_prompt_eval.py")
        patterns = [r"template", r"prompt", r"PromptTemplate"]
        assert any(
            re.search(p, content, re.IGNORECASE) for p in patterns
        ), "Script does not reference prompt templates"

    def test_accepts_test_cases(self):
        """Script must accept test cases with input variables and expected outputs."""
        content = self._read("scripts", "run_prompt_eval.py")
        patterns = [
            r"test.case",
            r"eval.case",
            r"scenario",
            r"example",
            r"input.*expected|expected.*input",
        ]
        assert any(
            re.search(p, content, re.IGNORECASE) for p in patterns
        ), "Script does not reference test cases"

    # ------------------------------------------------------------------
    # L1: Scoring metrics
    # ------------------------------------------------------------------

    def test_implements_at_least_two_scoring_metrics(self):
        """Script must implement at least two automated scoring metrics."""
        content = self._read("scripts", "run_prompt_eval.py")
        metric_patterns = [
            r"similarity",
            r"string_similarity",
            r"cosine",
            r"keyword",
            r"keyword_presence",
            r"exact_match",
            r"exact",
            r"format.*compliance",
            r"format.*check",
            r"bleu",
            r"rouge",
            r"f1",
            r"semantic",
            r"relevance",
            r"score",
            r"metric",
        ]
        matches = sum(
            1 for p in metric_patterns if re.search(p, content, re.IGNORECASE)
        )
        assert (
            matches >= 2
        ), f"Only {matches} scoring metric reference(s) found — need at least 2"

    def test_scores_recorded_per_result(self):
        """Each evaluation result must capture metric scores."""
        content = self._read("scripts", "run_prompt_eval.py")
        patterns = [
            r"score",
            r"result.*metric",
            r"metric.*score",
            r"scores\[",
            r"results\.append",
        ]
        assert any(
            re.search(p, content, re.IGNORECASE) for p in patterns
        ), "Script does not record scores per result"

    # ------------------------------------------------------------------
    # L1: Configuration loading
    # ------------------------------------------------------------------

    def test_supports_config_file_loading(self):
        """Script must support loading test cases from JSON or YAML."""
        content = self._read("scripts", "run_prompt_eval.py")
        patterns = [
            r"json\.load",
            r"yaml\.safe_load",
            r"yaml\.load",
            r"\.json",
            r"\.yaml",
            r"\.yml",
            r"argparse",
            r"config.*file",
        ]
        assert any(
            re.search(p, content) for p in patterns
        ), "Script does not support loading configuration from a file"

    def test_supports_model_parameters(self):
        """Script must support configurable model parameters."""
        content = self._read("scripts", "run_prompt_eval.py")
        patterns = [r"temperature", r"max_tokens", r"model", r"model_name"]
        assert any(
            re.search(p, content, re.IGNORECASE) for p in patterns
        ), "Script does not support configurable model parameters"

    # ------------------------------------------------------------------
    # L2: Report generation
    # ------------------------------------------------------------------

    def test_generates_summary_report(self):
        """Script must generate a summary report with pass/fail rates."""
        content = self._read("scripts", "run_prompt_eval.py")
        report_patterns = [
            r"summary",
            r"report",
            r"pass.*rate|rate.*pass",
            r"average.*score|score.*average",
            r"print.*result|print.*summary",
        ]
        assert any(
            re.search(p, content, re.IGNORECASE) for p in report_patterns
        ), "Script does not generate a summary report"

    def test_supports_structured_output(self):
        """Script must support JSON or CSV export of detailed results."""
        content = self._read("scripts", "run_prompt_eval.py")
        export_patterns = [
            r"json\.dump",
            r"csv\.writer",
            r"to_csv",
            r"to_json",
            r"\.json",
            r"\.csv",
            r"output.*file",
        ]
        assert any(
            re.search(p, content) for p in export_patterns
        ), "Script does not support structured output export (JSON/CSV)"

    # ------------------------------------------------------------------
    # L2: Quality checks
    # ------------------------------------------------------------------

    def test_results_capture_prompt_and_inputs(self):
        """Each result must capture the prompt used and the input variables."""
        content = self._read("scripts", "run_prompt_eval.py")
        patterns = [
            r"prompt.*input|input.*prompt",
            r"variables",
            r"template.*result|result.*template",
        ]
        assert any(
            re.search(p, content, re.IGNORECASE) for p in patterns
        ), "Results do not capture prompt and input information"

    def test_results_capture_generated_output(self):
        """Each result must capture the generated output."""
        content = self._read("scripts", "run_prompt_eval.py")
        patterns = [r"output", r"response", r"generated", r"completion"]
        assert any(
            re.search(p, content, re.IGNORECASE) for p in patterns
        ), "Results do not capture generated output"
