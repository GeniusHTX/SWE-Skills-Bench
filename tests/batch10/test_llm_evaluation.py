"""
Test for 'llm-evaluation' skill — LLM evaluation with HELM
Validates that the Agent implemented LLM evaluation patterns using
the HELM framework.
"""

import os
import re

import pytest


class TestLlmEvaluation:
    """Verify LLM evaluation implementation with HELM."""

    REPO_DIR = "/workspace/helm"

    def test_evaluation_config_exists(self):
        """Evaluation configuration file must exist."""
        found = False
        for root, dirs, files in os.walk(self.REPO_DIR):
            for f in files:
                if f.endswith((".py", ".yaml", ".yml", ".json")):
                    path = os.path.join(root, f)
                    with open(path, "r", errors="ignore") as fh:
                        content = fh.read()
                    if re.search(r"[Ee]val|[Bb]enchmark|[Ss]cenario|RunSpec", content):
                        found = True
                        break
            if found:
                break
        assert found, "No evaluation config found"

    def test_metric_definitions(self):
        """Evaluation metrics must be defined."""
        found = False
        for root, dirs, files in os.walk(self.REPO_DIR):
            for f in files:
                if f.endswith(".py"):
                    path = os.path.join(root, f)
                    with open(path, "r", errors="ignore") as fh:
                        content = fh.read()
                    if re.search(r"[Mm]etric|accuracy|f1_score|bleu|rouge|exact_match|perplexity", content):
                        found = True
                        break
            if found:
                break
        assert found, "No metric definitions found"

    def test_scenario_or_benchmark_class(self):
        """A Scenario or benchmark class must exist."""
        found = False
        for root, dirs, files in os.walk(self.REPO_DIR):
            for f in files:
                if f.endswith(".py"):
                    path = os.path.join(root, f)
                    with open(path, "r", errors="ignore") as fh:
                        content = fh.read()
                    if re.search(r"class\s+\w*(Scenario|Benchmark|Eval)\w*", content):
                        found = True
                        break
            if found:
                break
        assert found, "No Scenario or benchmark class found"

    def test_adapter_or_model_interface(self):
        """Model adapter or interface must be defined."""
        found = False
        for root, dirs, files in os.walk(self.REPO_DIR):
            for f in files:
                if f.endswith(".py"):
                    path = os.path.join(root, f)
                    with open(path, "r", errors="ignore") as fh:
                        content = fh.read()
                    if re.search(r"[Aa]dapter|[Mm]odel[Cc]lient|[Ll]anguage[Mm]odel|WindowService", content):
                        found = True
                        break
            if found:
                break
        assert found, "No model adapter or interface found"

    def test_prompt_construction(self):
        """Evaluation must construct prompts for the model."""
        found = False
        for root, dirs, files in os.walk(self.REPO_DIR):
            for f in files:
                if f.endswith(".py"):
                    path = os.path.join(root, f)
                    with open(path, "r", errors="ignore") as fh:
                        content = fh.read()
                    if re.search(r"[Pp]rompt|[Rr]equest|[Ii]nstance|get_instances|construct", content):
                        found = True
                        break
            if found:
                break
        assert found, "No prompt construction found"

    def test_run_spec_or_config(self):
        """RunSpec or evaluation run configuration must exist."""
        found = False
        for root, dirs, files in os.walk(self.REPO_DIR):
            for f in files:
                if f.endswith(".py"):
                    path = os.path.join(root, f)
                    with open(path, "r", errors="ignore") as fh:
                        content = fh.read()
                    if re.search(r"RunSpec|run_spec|EvalConfig|eval_config|BenchmarkConfig", content):
                        found = True
                        break
            if found:
                break
        assert found, "No RunSpec or evaluation config found"

    def test_output_or_results_collection(self):
        """Evaluation must collect and output results."""
        found = False
        for root, dirs, files in os.walk(self.REPO_DIR):
            for f in files:
                if f.endswith(".py"):
                    path = os.path.join(root, f)
                    with open(path, "r", errors="ignore") as fh:
                        content = fh.read()
                    if re.search(r"[Rr]esult|[Oo]utput|[Ss]tat|[Ss]core|aggregate|summarize", content):
                        if re.search(r"[Mm]etric|[Ee]val|[Bb]enchmark", content):
                            found = True
                            break
            if found:
                break
        assert found, "No results collection found"

    def test_data_loading(self):
        """Evaluation must load or generate test data."""
        found = False
        for root, dirs, files in os.walk(self.REPO_DIR):
            for f in files:
                if f.endswith(".py"):
                    path = os.path.join(root, f)
                    with open(path, "r", errors="ignore") as fh:
                        content = fh.read()
                    if re.search(r"load|download|dataset|read|instances|examples|samples", content, re.IGNORECASE):
                        if re.search(r"[Ss]cenario|[Bb]enchmark|[Ee]val", content):
                            found = True
                            break
            if found:
                break
        assert found, "No data loading found"

    def test_tokenization_or_windowing(self):
        """Evaluation should handle tokenization or context windowing."""
        found = False
        for root, dirs, files in os.walk(self.REPO_DIR):
            for f in files:
                if f.endswith(".py"):
                    path = os.path.join(root, f)
                    with open(path, "r", errors="ignore") as fh:
                        content = fh.read()
                    if re.search(r"token|window|truncat|max_length|context_length|WindowService", content, re.IGNORECASE):
                        found = True
                        break
            if found:
                break
        assert found, "No tokenization or windowing found"

    def test_test_file_exists(self):
        """Test file for evaluation code must exist."""
        found = False
        for root, dirs, files in os.walk(self.REPO_DIR):
            for f in files:
                if f.startswith("test_") and f.endswith(".py"):
                    path = os.path.join(root, f)
                    with open(path, "r", errors="ignore") as fh:
                        content = fh.read()
                    if re.search(r"[Ee]val|[Mm]etric|[Ss]cenario|[Bb]enchmark", content):
                        found = True
                        break
            if found:
                break
        assert found, "No test file for evaluation code"
