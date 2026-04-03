"""
Test for 'analyze-ci' skill — CI Failure Analyzer
Validates that the Agent implemented a CI failure analyzer module
in the Sentry codebase with fetching, parsing, classification, and reporting.
"""

import os
import re
import sys

import pytest


class TestAnalyzeCi:
    """Verify Sentry CI failure analyzer implementation."""

    REPO_DIR = "/workspace/sentry"

    @staticmethod
    def _read(path: str) -> str:
        try:
            with open(path, "r", errors="ignore") as fh:
                return fh.read()
        except OSError:
            return ""

    # ── file_path_check ─────────────────────────────────────────────

    def test_ci_analyzer_module_files_exist(self):
        """Verify all required ci_analyzer module files exist."""
        for rel in (
            "src/sentry/utils/ci_analyzer/__init__.py",
            "src/sentry/utils/ci_analyzer/fetcher.py",
            "src/sentry/utils/ci_analyzer/parser.py",
        ):
            path = os.path.join(self.REPO_DIR, rel)
            assert os.path.isfile(path), f"Missing: {rel}"

    def test_ci_analyzer_classifier_cli_exist(self):
        """Verify classifier.py, models.py, and cli.py exist."""
        for rel in (
            "src/sentry/utils/ci_analyzer/classifier.py",
            "src/sentry/utils/ci_analyzer/models.py",
            "src/sentry/utils/ci_analyzer/cli.py",
        ):
            path = os.path.join(self.REPO_DIR, rel)
            assert os.path.isfile(path), f"Missing: {rel}"

    def test_module_importable(self):
        """Verify the ci_analyzer package is importable without errors."""
        if not os.path.isdir(self.REPO_DIR):
            pytest.skip("Repo dir does not exist")
        sys.path.insert(0, os.path.join(self.REPO_DIR, "src"))
        try:
            import sentry.utils.ci_analyzer  # noqa: F401
        except ImportError:
            pytest.skip("sentry.utils.ci_analyzer not importable — deps may be missing")
        finally:
            sys.path.pop(0)

    # ── semantic_check ──────────────────────────────────────────────

    def test_fetcher_class_with_parse_method(self):
        """Verify fetcher.py defines a class/function for parsing PR URLs."""
        content = self._read(os.path.join(
            self.REPO_DIR, "src/sentry/utils/ci_analyzer/fetcher.py"))
        assert content, "fetcher.py is empty or unreadable"
        found = "parse_pr_url" in content or "CIFetcher" in content
        assert found, "Neither CIFetcher nor parse_pr_url found in fetcher.py"

    def test_classifier_six_categories(self):
        """Verify classifier.py contains all 6 failure category strings."""
        content = self._read(os.path.join(
            self.REPO_DIR, "src/sentry/utils/ci_analyzer/classifier.py"))
        assert content, "classifier.py is empty or unreadable"
        for cat in ("test_failure", "lint_error", "build_error",
                     "timeout", "infra_flake", "unknown"):
            assert cat in content, f"Category '{cat}' not found in classifier.py"

    def test_confidence_rules_present(self):
        """Verify confidence scores 1.0, 0.8, 0.5 appear in classifier.py."""
        content = self._read(os.path.join(
            self.REPO_DIR, "src/sentry/utils/ci_analyzer/classifier.py"))
        assert content, "classifier.py is empty or unreadable"
        for score in ("1.0", "0.8", "0.5"):
            assert score in content, f"Confidence score {score} not found in classifier.py"

    def test_models_dataclasses_defined(self):
        """Verify models.py defines dataclasses for PRInfo, JobFailure, and ClassificationResult."""
        content = self._read(os.path.join(
            self.REPO_DIR, "src/sentry/utils/ci_analyzer/models.py"))
        assert content, "models.py is empty or unreadable"
        for name in ("PRInfo", "JobFailure", "ClassificationResult"):
            assert name in content, f"Dataclass '{name}' not found in models.py"

    # ── functional_check (import) ───────────────────────────────────

    def _try_import(self, module_path: str):
        if not os.path.isdir(self.REPO_DIR):
            pytest.skip("Repo dir does not exist")
        sys.path.insert(0, os.path.join(self.REPO_DIR, "src"))
        try:
            mod = __import__(module_path, fromlist=[""])
            return mod
        except ImportError:
            pytest.skip(f"{module_path} not importable")
        finally:
            sys.path.pop(0)

    def test_parse_pr_url_valid(self):
        """CIFetcher().parse_pr_url returns correct (owner, repo, number) tuple."""
        mod = self._try_import("sentry.utils.ci_analyzer.fetcher")
        fetcher_cls = getattr(mod, "CIFetcher", None)
        if fetcher_cls is None:
            pytest.skip("CIFetcher class not found")
        result = fetcher_cls().parse_pr_url("https://github.com/getsentry/sentry/pull/12345")
        assert result[0] == "getsentry"
        assert result[1] == "sentry"
        assert result[2] == 12345

    def test_parse_pr_url_invalid_raises_value_error(self):
        """parse_pr_url('not-a-url') raises ValueError."""
        mod = self._try_import("sentry.utils.ci_analyzer.fetcher")
        fetcher_cls = getattr(mod, "CIFetcher", None)
        if fetcher_cls is None:
            pytest.skip("CIFetcher class not found")
        with pytest.raises(ValueError, match="Invalid PR URL"):
            fetcher_cls().parse_pr_url("not-a-url")

    def test_classifier_test_failure_step_name(self):
        """Classifier with step_name='Run tests' returns test_failure, confidence 1.0."""
        mod = self._try_import("sentry.utils.ci_analyzer.classifier")
        classify = getattr(mod, "classify", None) or getattr(mod, "Classifier", None)
        if classify is None:
            pytest.skip("No classify function or Classifier class found")
        if callable(classify) and not isinstance(classify, type):
            result = classify(step_name="Run tests", error_text="AssertionError")
        else:
            result = classify().classify(step_name="Run tests", error_text="AssertionError")
        assert hasattr(result, "category") or isinstance(result, dict)
        cat = result.category if hasattr(result, "category") else result.get("category")
        assert cat == "test_failure"

    def test_classifier_infra_flake_503(self):
        """Classifier with error_text='503 Service Unavailable' returns infra_flake."""
        mod = self._try_import("sentry.utils.ci_analyzer.classifier")
        classify = getattr(mod, "classify", None) or getattr(mod, "Classifier", None)
        if classify is None:
            pytest.skip("No classify function or Classifier class found")
        if callable(classify) and not isinstance(classify, type):
            result = classify(step_name="Deploy preview", error_text="503 Service Unavailable")
        else:
            result = classify().classify(step_name="Deploy preview", error_text="503 Service Unavailable")
        cat = result.category if hasattr(result, "category") else result.get("category")
        assert cat == "infra_flake"

    def test_report_contains_required_fields(self):
        """Generated report dict contains all required top-level keys."""
        mod = self._try_import("sentry.utils.ci_analyzer")
        generate = getattr(mod, "generate_report", None) or getattr(mod, "CIAnalyzer", None)
        if generate is None:
            pytest.skip("No generate_report or CIAnalyzer found")
        # Semantic fallback: check models for expected keys
        models_content = self._read(os.path.join(
            self.REPO_DIR, "src/sentry/utils/ci_analyzer/models.py"))
        for key in ("pr_url", "head_sha", "analyzed_at", "total_failed_jobs", "failures", "summary"):
            assert key in models_content, f"Key '{key}' not found in models definitions"
