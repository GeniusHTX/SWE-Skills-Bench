"""
Test for 'llm-evaluation' skill — LLM Evaluation
Validates that the Agent created an LLM evaluation demo with config, sample inputs,
and structured output in the HELM repository.
"""

import os
import subprocess
import json
import pytest


class TestLlmEvaluation:
    """Verify LLM evaluation demo in HELM."""

    REPO_DIR = "/workspace/helm"

    # ------------------------------------------------------------------
    # L1: file existence & syntax
    # ------------------------------------------------------------------

    def test_eval_demo_exists(self):
        """examples/llm_eval_demo.py must exist."""
        fpath = os.path.join(self.REPO_DIR, "examples", "llm_eval_demo.py")
        assert os.path.isfile(fpath), "llm_eval_demo.py not found"

    def test_eval_demo_compiles(self):
        """llm_eval_demo.py must compile."""
        result = subprocess.run(
            ["python", "-m", "py_compile", "examples/llm_eval_demo.py"],
            cwd=self.REPO_DIR,
            capture_output=True,
            text=True,
            timeout=30,
        )
        assert result.returncode == 0, f"Syntax error:\n{result.stderr}"

    def test_eval_config_exists(self):
        """examples/eval_config.yaml must exist."""
        fpath = os.path.join(self.REPO_DIR, "examples", "eval_config.yaml")
        assert os.path.isfile(fpath), "eval_config.yaml not found"

    # ------------------------------------------------------------------
    # L2: structural & content verification
    # ------------------------------------------------------------------

    def _read_demo_source(self):
        fpath = os.path.join(self.REPO_DIR, "examples", "llm_eval_demo.py")
        with open(fpath, "r", encoding="utf-8") as f:
            return f.read()

    def test_config_is_valid_yaml(self):
        """eval_config.yaml must be valid YAML."""
        import yaml

        fpath = os.path.join(self.REPO_DIR, "examples", "eval_config.yaml")
        with open(fpath, "r") as f:
            config = yaml.safe_load(f)
        assert isinstance(config, dict), "eval_config.yaml must be a YAML mapping"

    def test_demo_loads_config(self):
        """Demo must load configuration."""
        source = self._read_demo_source()
        load_patterns = ["yaml", "json", "config", "load"]
        found = sum(1 for p in load_patterns if p in source.lower())
        assert found >= 2, "No configuration loading found in demo"

    def test_demo_has_score_output(self):
        """Demo must produce score in its output."""
        source = self._read_demo_source()
        assert "score" in source.lower(), "No score output in demo"

    def test_demo_has_labels_or_metrics(self):
        """Demo must include labels or detailed metrics."""
        source = self._read_demo_source()
        metric_patterns = ["label", "metric", "accuracy", "precision", "recall", "f1"]
        found = sum(1 for p in metric_patterns if p in source.lower())
        assert found >= 1, "No labels/metrics output in demo"

    def test_demo_runs_successfully(self):
        """llm_eval_demo.py must exit with code 0."""
        result = subprocess.run(
            ["python", "examples/llm_eval_demo.py"],
            cwd=self.REPO_DIR,
            capture_output=True,
            text=True,
            timeout=120,
        )
        assert result.returncode == 0, f"Demo failed:\n{result.stderr}"

    def test_output_contains_score(self):
        """Output must include a score value."""
        result = subprocess.run(
            ["python", "examples/llm_eval_demo.py"],
            cwd=self.REPO_DIR,
            capture_output=True,
            text=True,
            timeout=120,
        )
        if result.returncode != 0:
            pytest.skip(f"Demo failed: {result.stderr[:500]}")
        combined = result.stdout + result.stderr
        assert (
            "score" in combined.lower()
        ), f"'score' not found in output:\n{combined[:2000]}"

    def test_sample_inputs_present(self):
        """Demo or config should include sample evaluation inputs."""
        source = self._read_demo_source()
        import yaml

        config_path = os.path.join(self.REPO_DIR, "examples", "eval_config.yaml")
        with open(config_path, "r") as f:
            config_content = f.read()
        combined = source + config_content
        input_patterns = ["sample", "input", "prompt", "question", "example"]
        found = sum(1 for p in input_patterns if p in combined.lower())
        assert found >= 2, "No sample evaluation inputs found"

    def test_can_run_without_external_api(self):
        """Demo should run locally without external API calls."""
        source = self._read_demo_source()
        # Should use mock model or local evaluation
        has_mock = any(
            p in source.lower() for p in ["mock", "fake", "local", "dummy", "test_data"]
        )
        has_api_key = "API_KEY" in source and "os.environ.get" not in source
        assert (
            has_mock or not has_api_key
        ), "Demo requires external API without fallback"

    def test_generates_report_file(self):
        """Demo should generate an evaluation report file."""
        result = subprocess.run(
            ["python", "examples/llm_eval_demo.py"],
            cwd=self.REPO_DIR,
            capture_output=True,
            text=True,
            timeout=120,
        )
        if result.returncode != 0:
            pytest.skip(f"Demo failed: {result.stderr[:500]}")
        # Check for generated report files
        report_extensions = [".json", ".csv"]
        found_reports = []
        for root, dirs, files in os.walk(self.REPO_DIR):
            for f in files:
                if any(f.endswith(ext) for ext in report_extensions):
                    fpath = os.path.join(root, f)
                    if (
                        os.path.getmtime(fpath)
                        > os.path.getmtime(
                            os.path.join(self.REPO_DIR, "examples", "llm_eval_demo.py")
                        )
                        - 60
                    ):
                        found_reports.append(fpath)
            if len(found_reports) > 5:
                break
        # Or check stdout is JSON
        try:
            json.loads(result.stdout.strip())
            found_reports.append("stdout")
        except (json.JSONDecodeError, ValueError):
            pass
        assert (
            len(found_reports) >= 1
        ), "No evaluation report generated (JSON/CSV file or JSON stdout)"
