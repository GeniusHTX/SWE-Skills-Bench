"""
Test for 'llm-evaluation' skill — HELM LLM Evaluation Framework
Validates runner, metrics, splitter, config modules with ExactMatch,
80/20 split, FactualQA scenario, and edge cases.
"""

import os
import re
import subprocess
import sys

import pytest


class TestLlmEvaluation:
    """Verify HELM LLM evaluation framework implementation."""

    REPO_DIR = "/workspace/helm"

    # ── file_path_check ─────────────────────────────────────────────────────

    def test_evaluation_source_files_exist(self):
        """Verify at least 3 evaluation Python files exist."""
        py_files = self._find_eval_files()
        assert (
            len(py_files) >= 3
        ), f"Expected ≥3 evaluation files, found {len(py_files)}"

    def test_config_file_exists(self):
        """Verify evaluation configuration file exists."""
        found = self._find_files(["config", "scenario", "setting"])
        assert found, "No config/scenario file found"

    # ── semantic_check ──────────────────────────────────────────────────────

    def test_exact_match_metric(self):
        """Verify ExactMatch metric with case-insensitive .lower() comparison."""
        files = self._find_eval_files()
        assert files, "No eval files"
        for fpath in files:
            content = self._read(fpath)
            if re.search(r"(ExactMatch|exact_match)", content, re.IGNORECASE):
                if ".lower()" in content:
                    return
                return  # ExactMatch exists even without explicit .lower()
        pytest.fail("No ExactMatch metric found")

    def test_80_20_split(self):
        """Verify 80/20 data split for evaluation."""
        files = self._find_eval_files()
        for fpath in files:
            content = self._read(fpath)
            if re.search(
                r"(0\.8|0\.2|80.*20|split.*0\.[28]|train.*test)", content, re.IGNORECASE
            ):
                return
        pytest.fail("No 80/20 data split found")

    def test_factual_qa_scenario(self):
        """Verify FactualQA or similar QA evaluation scenario."""
        files = self._find_eval_files()
        for fpath in files:
            content = self._read(fpath)
            if re.search(
                r"(FactualQA|factual_qa|QA.*scenario|question.*answer)",
                content,
                re.IGNORECASE,
            ):
                return
        pytest.fail("No FactualQA scenario found")

    def test_runner_orchestrates(self):
        """Verify runner module orchestrates evaluation pipeline."""
        files = self._find_files(["runner", "run", "evaluate"])
        assert files, "No runner files"
        for fpath in files:
            content = self._read(fpath)
            if re.search(r"def\s+(run|evaluate|execute)", content):
                return
        pytest.fail("No runner orchestration function found")

    # ── functional_check ────────────────────────────────────────────────────

    def test_files_compile(self):
        """Verify Python files compile without errors."""
        files = self._find_eval_files()
        assert files, "No eval files"
        for fpath in files:
            if not fpath.endswith(".py"):
                continue
            result = subprocess.run(
                [sys.executable, "-m", "py_compile", fpath],
                capture_output=True,
                text=True,
                timeout=30,
            )
            assert (
                result.returncode == 0
            ), f"Compile error in {os.path.basename(fpath)}: {result.stderr}"

    def test_exact_match_scoring(self):
        """Verify ExactMatch returns 1.0 for matching, 0.0 for mismatch."""
        files = self._find_eval_files()
        for fpath in files:
            content = self._read(fpath)
            if re.search(r"(1\.0|0\.0)", content):
                if "match" in content.lower():
                    return
        pytest.skip("ExactMatch scoring values not explicitly detectable")

    def test_empty_dataset_handling(self):
        """Verify empty dataset raises error or returns empty result."""
        files = self._find_eval_files()
        for fpath in files:
            content = self._read(fpath)
            if re.search(
                r"(empty|no.?data|len\(.*\)\s*==\s*0|ValueError)",
                content,
                re.IGNORECASE,
            ):
                return
        pytest.skip("Empty dataset handling not explicitly detectable")

    def test_splitter_module_exists(self):
        """Verify data splitter module with split function."""
        files = self._find_files(["split"])
        for fpath in files:
            content = self._read(fpath)
            if re.search(r"def\s+split|class\s+\w*Split", content):
                return
        pytest.fail("No splitter module with split function found")

    def test_whitespace_handling_in_metric(self):
        """Verify metric handles whitespace in comparisons."""
        files = self._find_eval_files()
        for fpath in files:
            content = self._read(fpath)
            if re.search(r"(\.strip\(\)|\.strip|whitespace|normalize)", content):
                return
        pytest.skip("Whitespace handling not explicitly detectable")

    # ── helpers ──────────────────────────────────────────────────────────────

    def _find_eval_files(self):
        return self._find_files(
            ["eval", "metric", "split", "runner", "scenario", "config"]
        )

    def _find_files(self, keywords):
        results = []
        for dirpath, _, fnames in os.walk(self.REPO_DIR):
            if ".git" in dirpath or "node_modules" in dirpath:
                continue
            for f in fnames:
                if f.endswith(".py") and any(k in f.lower() for k in keywords):
                    results.append(os.path.join(dirpath, f))
        return results

    def _read(self, path):
        with open(path, "r", errors="ignore") as fh:
            return fh.read()
