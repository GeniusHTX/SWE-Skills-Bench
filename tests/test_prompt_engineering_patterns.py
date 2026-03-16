"""
Test for 'prompt-engineering-patterns' skill — Prompt Engineering Patterns
Validates that the Agent implemented prompt templates and automated evaluation
in the LangChain repository.
"""

import os
import subprocess
import json
import pytest


class TestPromptEngineeringPatterns:
    """Verify prompt engineering template system and evaluation."""

    REPO_DIR = "/workspace/langchain"

    # ------------------------------------------------------------------
    # L1: file existence & syntax
    # ------------------------------------------------------------------

    def test_eval_script_exists(self):
        """scripts/run_prompt_eval.py must exist."""
        fpath = os.path.join(self.REPO_DIR, "scripts", "run_prompt_eval.py")
        assert os.path.isfile(fpath), "run_prompt_eval.py not found"

    def test_eval_script_compiles(self):
        """run_prompt_eval.py must compile."""
        result = subprocess.run(
            ["python", "-m", "py_compile", "scripts/run_prompt_eval.py"],
            cwd=self.REPO_DIR,
            capture_output=True,
            text=True,
            timeout=30,
        )
        assert result.returncode == 0, f"Syntax error:\n{result.stderr}"

    def test_templates_directory_exists(self):
        """examples/prompt_templates/ directory must exist."""
        dpath = os.path.join(self.REPO_DIR, "examples", "prompt_templates")
        assert os.path.isdir(dpath), "prompt_templates directory not found"

    # ------------------------------------------------------------------
    # L2: functional verification
    # ------------------------------------------------------------------

    def test_eval_script_runs(self):
        """run_prompt_eval.py must execute with exit code 0."""
        result = subprocess.run(
            ["python", "scripts/run_prompt_eval.py"],
            cwd=self.REPO_DIR,
            capture_output=True,
            text=True,
            timeout=120,
        )
        assert result.returncode == 0, f"Script failed:\n{result.stderr}"

    def test_eval_output_is_valid_json_or_csv(self):
        """Evaluation output should contain structured data (JSON/CSV)."""
        result = subprocess.run(
            ["python", "scripts/run_prompt_eval.py"],
            cwd=self.REPO_DIR,
            capture_output=True,
            text=True,
            timeout=120,
        )
        if result.returncode != 0:
            pytest.skip(f"Script failed: {result.stderr[:500]}")
        # Check if a report file was generated
        report_candidates = []
        for root, dirs, files in os.walk(self.REPO_DIR):
            for f in files:
                if f.endswith((".json", ".csv")) and "report" in f.lower():
                    report_candidates.append(os.path.join(root, f))
            if len(report_candidates) > 10:
                break
        # Or check stdout for JSON
        output = result.stdout.strip()
        is_json = False
        try:
            json.loads(output)
            is_json = True
        except (json.JSONDecodeError, ValueError):
            pass
        assert (
            is_json or len(report_candidates) >= 1
        ), "No structured report output found (JSON stdout or report file)"

    def test_template_files_present(self):
        """At least 2 prompt template files must exist."""
        dpath = os.path.join(self.REPO_DIR, "examples", "prompt_templates")
        if not os.path.isdir(dpath):
            pytest.skip("prompt_templates directory not found")
        files = os.listdir(dpath)
        template_files = [
            f
            for f in files
            if f.endswith((".json", ".yaml", ".yml", ".txt", ".md", ".py"))
        ]
        assert (
            len(template_files) >= 2
        ), f"Expected >= 2 template files, found {len(template_files)}: {template_files}"

    def test_source_has_json_schema(self):
        """Eval script or templates should follow a JSON schema structure."""
        fpath = os.path.join(self.REPO_DIR, "scripts", "run_prompt_eval.py")
        with open(fpath, "r", encoding="utf-8") as f:
            content = f.read()
        schema_fields = [
            "input_id",
            "prompt",
            "expected_output",
            "metadata",
            "score",
            "input",
            "output",
        ]
        found = sum(1 for sf in schema_fields if sf in content)
        assert found >= 3, f"Insufficient schema fields in eval script (found {found})"

    def test_pluggable_scorers(self):
        """Eval script should support pluggable scoring mechanisms."""
        fpath = os.path.join(self.REPO_DIR, "scripts", "run_prompt_eval.py")
        with open(fpath, "r", encoding="utf-8") as f:
            content = f.read()
        scorer_patterns = [
            "scorer",
            "score",
            "assert",
            "similarity",
            "evaluate",
            "metric",
        ]
        found = sum(1 for sp in scorer_patterns if sp in content.lower())
        assert found >= 2, "No scoring/evaluation mechanism found"

    def test_batch_evaluation_support(self):
        """Script should support batch evaluation of multiple prompts."""
        fpath = os.path.join(self.REPO_DIR, "scripts", "run_prompt_eval.py")
        with open(fpath, "r", encoding="utf-8") as f:
            content = f.read()
        batch_patterns = ["for ", "batch", "loop", "iterate", "results"]
        found = sum(1 for bp in batch_patterns if bp in content.lower())
        assert found >= 2, "No batch evaluation support found"

    def test_multiple_prompt_types(self):
        """Templates should cover multiple use cases."""
        dpath = os.path.join(self.REPO_DIR, "examples", "prompt_templates")
        if not os.path.isdir(dpath):
            pytest.skip("prompt_templates directory not found")
        all_content = ""
        for f in os.listdir(dpath):
            fpath = os.path.join(dpath, f)
            if os.path.isfile(fpath):
                with open(fpath, "r", encoding="utf-8", errors="replace") as fh:
                    all_content += fh.read() + "\n"
        categories = [
            "instruction",
            "conversation",
            "extract",
            "translat",
            "code",
            "evaluat",
        ]
        found = sum(1 for c in categories if c in all_content.lower())
        assert found >= 2, f"Only {found} prompt categories found in templates"
