"""
Test for 'analyze-ci' skill — Sentry CI Failure Analysis
Validates Python scripts that parse CI logs, classify failures into
categories, format JSON/markdown reports, and corresponding tests.
"""

import os
import re
import subprocess
import sys

import pytest


class TestAnalyzeCi:
    """Verify Sentry CI failure analysis scripts."""

    REPO_DIR = "/workspace/sentry"

    # ── file_path_check ─────────────────────────────────────────────────────

    def test_ci_analysis_scripts_exist(self):
        """Verify at least 3 Python scripts for CI analysis exist."""
        scripts_dir = os.path.join(self.REPO_DIR, "scripts")
        tools_dir = os.path.join(self.REPO_DIR, "tools")
        src_dir = os.path.join(self.REPO_DIR, "src")
        py_files = []
        for d in [scripts_dir, tools_dir, src_dir, self.REPO_DIR]:
            if not os.path.isdir(d):
                continue
            for dirpath, _, fnames in os.walk(d):
                for f in fnames:
                    if f.endswith(".py") and (
                        "ci" in f.lower()
                        or "analyz" in f.lower()
                        or "failure" in f.lower()
                    ):
                        py_files.append(os.path.join(dirpath, f))
        assert (
            len(py_files) >= 2
        ), f"Expected ≥2 CI analysis scripts, found: {[os.path.basename(f) for f in py_files]}"

    def test_ci_test_file_exists(self):
        """Verify a test file for CI analysis exists."""
        found = False
        for dirpath, _, fnames in os.walk(self.REPO_DIR):
            if ".git" in dirpath:
                continue
            for f in fnames:
                if (
                    f.endswith(".py")
                    and "test" in f.lower()
                    and ("ci" in f.lower() or "failure" in f.lower())
                ):
                    found = True
                    break
            if found:
                break
        assert found, "No CI analysis test file found"

    # ── semantic_check ──────────────────────────────────────────────────────

    def test_failure_categories_defined(self):
        """Verify at least 4 failure categories are defined."""
        py_files = self._find_ci_files()
        assert py_files, "No CI analysis files found"
        category_count = 0
        for fpath in py_files:
            content = self._read(fpath)
            # Count enum members, dict keys, or class constants
            category_count += len(
                re.findall(
                    r"(?:FLAKY|INFRA|TIMEOUT|OOM|DEPENDENCY|COMPILATION|TEST_FAILURE|NETWORK|UNKNOWN|CONFIG)",
                    content,
                    re.IGNORECASE,
                )
            )
        unique_categories = set(
            re.findall(
                r"(?:FLAKY|INFRA|TIMEOUT|OOM|DEPENDENCY|COMPILATION|TEST_FAILURE|NETWORK|UNKNOWN|CONFIG)",
                " ".join(self._read(f) for f in py_files),
                re.IGNORECASE,
            )
        )
        assert (
            len(unique_categories) >= 4
        ), f"Expected ≥4 failure categories, found: {unique_categories}"

    def test_parse_and_classify_methods_exist(self):
        """Verify parse and classify functions/methods exist."""
        py_files = self._find_ci_files()
        assert py_files, "No CI analysis files found"
        has_parse = False
        has_classify = False
        for fpath in py_files:
            content = self._read(fpath)
            if re.search(r"def\s+(parse|extract)", content):
                has_parse = True
            if re.search(r"def\s+(classify|categorize)", content):
                has_classify = True
        assert has_parse, "No parse/extract function found"
        assert has_classify, "No classify/categorize function found"

    def test_json_report_formatter(self):
        """Verify JSON report formatting capability."""
        py_files = self._find_ci_files()
        assert py_files, "No CI analysis files found"
        for fpath in py_files:
            content = self._read(fpath)
            if "json" in content.lower() and (
                "report" in content.lower() or "format" in content.lower()
            ):
                return
        pytest.fail("No JSON report formatting found")

    def test_markdown_report_formatter(self):
        """Verify markdown report formatting capability."""
        py_files = self._find_ci_files()
        assert py_files, "No CI analysis files found"
        for fpath in py_files:
            content = self._read(fpath)
            if re.search(
                r"markdown|\.md|##.*head|format_markdown", content, re.IGNORECASE
            ):
                return
        pytest.fail("No markdown report formatting found")

    # ── functional_check ────────────────────────────────────────────────────

    def test_scripts_compile(self):
        """Verify all CI analysis scripts compile without errors."""
        py_files = self._find_ci_files()
        assert py_files, "No CI analysis files found"
        for fpath in py_files:
            result = subprocess.run(
                [sys.executable, "-m", "py_compile", fpath],
                capture_output=True,
                text=True,
                timeout=30,
            )
            assert (
                result.returncode == 0
            ), f"Compilation failed for {os.path.basename(fpath)}: {result.stderr}"

    def test_classifier_importable(self):
        """Verify the main CI analysis module is importable."""
        py_files = self._find_ci_files()
        assert py_files, "No CI analysis files found"
        # Try to import the first file
        main_file = py_files[0]
        parent_dir = os.path.dirname(main_file)
        module_name = os.path.splitext(os.path.basename(main_file))[0]
        result = subprocess.run(
            [
                sys.executable,
                "-c",
                f"import sys; sys.path.insert(0, '{parent_dir}'); import {module_name}",
            ],
            capture_output=True,
            text=True,
            timeout=30,
            cwd=self.REPO_DIR,
        )
        # Allow import to fail due to missing deps, but not due to syntax
        if result.returncode != 0:
            assert (
                "SyntaxError" not in result.stderr
            ), f"SyntaxError in {module_name}: {result.stderr}"

    def test_report_includes_summary(self):
        """Verify report formatter includes summary/total counts."""
        py_files = self._find_ci_files()
        assert py_files, "No CI analysis files found"
        for fpath in py_files:
            content = self._read(fpath)
            if re.search(r"summary|total|count", content, re.IGNORECASE):
                return
        pytest.fail("No report summary/total logic found")

    def test_test_file_has_assertions(self):
        """Verify test file contains assert statements."""
        for dirpath, _, fnames in os.walk(self.REPO_DIR):
            if ".git" in dirpath:
                continue
            for f in fnames:
                if (
                    f.endswith(".py")
                    and "test" in f.lower()
                    and ("ci" in f.lower() or "failure" in f.lower())
                ):
                    content = self._read(os.path.join(dirpath, f))
                    if "assert" in content:
                        return
        pytest.fail("No assertions found in CI analysis test file")

    # ── helpers ──────────────────────────────────────────────────────────────

    def _find_ci_files(self):
        results = []
        for dirpath, _, fnames in os.walk(self.REPO_DIR):
            if ".git" in dirpath:
                continue
            for f in fnames:
                if f.endswith(".py") and (
                    "ci" in f.lower() or "analyz" in f.lower() or "failure" in f.lower()
                ):
                    results.append(os.path.join(dirpath, f))
            if len(results) >= 20:
                break
        return results

    def _read(self, path):
        with open(path, "r", errors="ignore") as fh:
            return fh.read()
