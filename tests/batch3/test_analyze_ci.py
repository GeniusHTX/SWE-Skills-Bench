"""
Tests for the analyze-ci skill.
Verifies that the Sentry CI failure analyzer module (CILogParser, generate_report,
FailureCategory, FailureReport) is correctly implemented with proper file structure,
semantic integrity, and functional behavior via direct import.
"""

import importlib
import os
import sys

import pytest

REPO_DIR = "/workspace/sentry"


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _path(rel: str) -> str:
    return os.path.join(REPO_DIR, rel)


def _read(rel: str) -> str:
    full = _path(rel)
    if not os.path.isfile(full):
        pytest.skip(f"File not found: {full}")
    with open(full, encoding="utf-8", errors="replace") as fh:
        return fh.read()


def _try_import_ci_analyzer():
    """Attempt to import ci_analyzer from the sentry package; skip if unavailable."""
    src_path = os.path.join(REPO_DIR, "src")
    if src_path not in sys.path:
        sys.path.insert(0, src_path)
    try:
        module = importlib.import_module("sentry.utils.ci_analyzer")
        return module
    except ImportError as exc:
        pytest.skip(f"Cannot import sentry.utils.ci_analyzer: {exc}")


# ---------------------------------------------------------------------------
# File path checks
# ---------------------------------------------------------------------------


class TestAnalyzeCi:
    """Test suite for the CI failure analyzer skill in the Sentry project."""

    def test_ci_analyzer_module_file_exists(self):
        """Verify ci_analyzer.py is created at the expected path."""
        target = _path("src/sentry/utils/ci_analyzer.py")
        assert os.path.isfile(target), f"ci_analyzer.py not found: {target}"
        assert os.path.getsize(target) > 0, "ci_analyzer.py must be non-empty"

    def test_ci_models_file_exists(self):
        """Verify ci_models.py is created alongside ci_analyzer.py."""
        target = _path("src/sentry/utils/ci_models.py")
        assert os.path.isfile(target), f"ci_models.py not found: {target}"

    # -----------------------------------------------------------------------
    # Semantic checks
    # -----------------------------------------------------------------------

    def test_ci_analyzer_defines_cilogparser_class(self):
        """Verify ci_analyzer.py defines the CILogParser class with a parse method."""
        content = _read("src/sentry/utils/ci_analyzer.py")
        assert (
            "class CILogParser" in content
        ), "ci_analyzer.py must define 'class CILogParser'"
        has_parse = "def parse" in content or "def parse_log" in content
        assert has_parse, "CILogParser must define a 'parse' or 'parse_log' method"

    def test_ci_analyzer_defines_generate_report(self):
        """Verify ci_analyzer.py defines the generate_report function."""
        content = _read("src/sentry/utils/ci_analyzer.py")
        assert (
            "def generate_report" in content
        ), "ci_analyzer.py must define 'def generate_report'"

    def test_ci_models_defines_failure_category_enum(self):
        """Verify ci_models.py defines a FailureCategory enum with at least 7 categories."""
        content = _read("src/sentry/utils/ci_models.py")
        lower = content.lower()
        assert (
            "failurecategory" in lower or "failure_category" in lower
        ), "ci_models.py must define a FailureCategory enum or equivalent"
        # Count category member lines - heuristic: look for enum string values or member assignments
        import re

        # Count ALL_CAPS identifiers or string enum values inside the FailureCategory block
        members = re.findall(r"\b([A-Z_]{3,})\s*=", content)
        enum_keywords = re.findall(r"['\"]([a-zA-Z_]+)['\"]", content)
        total_candidates = len(members) + len(enum_keywords)
        assert (
            total_candidates >= 7
        ), "FailureCategory must have at least 7 distinct category members"

    def test_failure_report_dataclass_defined(self):
        """Verify ci_models.py defines a FailureReport dataclass or class."""
        content = _read("src/sentry/utils/ci_models.py")
        assert "FailureReport" in content, "ci_models.py must define 'FailureReport'"

    # -----------------------------------------------------------------------
    # Functional checks (import)
    # -----------------------------------------------------------------------

    def test_parse_error_annotation_returns_failure(self):
        """Verify CILogParser.parse extracts ::error:: annotations from log output."""
        mod = _try_import_ci_analyzer()
        parser = mod.CILogParser()
        log = "::error file=src/auth.py,line=42::Missing import statement\n::error file=src/db.py,line=10::Connection timeout"
        result = parser.parse(log)
        # result could be an object with .failures or a plain list
        failures = (
            getattr(result, "failures", result)
            if not isinstance(result, list)
            else result
        )
        assert failures is not None, "parse() must not return None"
        assert len(failures) >= 2, f"Expected >= 2 failures, got {len(failures)}"

    def test_generate_report_returns_report_object(self):
        """Verify generate_report returns a FailureReport object with expected attributes."""
        mod = _try_import_ci_analyzer()
        report = mod.generate_report("::error file=test.py,line=1::Test failed")
        assert report is not None, "generate_report must not return None"
        assert hasattr(
            report, "failures"
        ), "FailureReport must have a 'failures' attribute"
        assert hasattr(
            report, "root_cause"
        ), "FailureReport must have a 'root_cause' attribute"

    def test_empty_log_returns_empty_failures(self):
        """Verify CILogParser.parse returns empty failures list for empty log."""
        mod = _try_import_ci_analyzer()
        parser = mod.CILogParser()
        result = parser.parse("")
        failures = (
            getattr(result, "failures", result)
            if not isinstance(result, list)
            else result
        )
        failures = failures or []
        assert len(failures) == 0, "Empty log must produce zero failures"

    def test_flaky_detection_with_previous_results(self):
        """Verify CILogParser marks a test as flaky when it appears in previous_results."""
        mod = _try_import_ci_analyzer()
        try:
            parser = mod.CILogParser(previous_results=["test_auth_login"])
        except TypeError:
            pytest.skip("CILogParser does not accept previous_results parameter")
        log = "::error file=tests/test_auth.py,line=20::test_auth_login FAILED"
        result = parser.parse(log)
        failures = (
            getattr(result, "failures", result)
            if not isinstance(result, list)
            else result
        )
        failures = failures or []
        if not failures:
            pytest.skip("No failures parsed; cannot verify flaky detection")
        flaky_found = any(
            getattr(f, "is_flaky", False)
            or getattr(f, "category", "") in ("flaky", "FLAKY")
            for f in failures
        )
        assert (
            flaky_found
        ), "At least one failure must be flagged as flaky when test existed in previous_results"

    def test_root_cause_extraction_from_multiple_errors(self):
        """Verify generate_report extracts a root cause from multiple cascading errors."""
        mod = _try_import_ci_analyzer()
        log = (
            "::error file=src/db.py,line=5::ConnectionError\n"
            "::error file=src/auth.py,line=12::DatabaseError caused by ConnectionError\n"
            "::error file=tests/test_login.py,line=30::test_login FAILED"
        )
        report = mod.generate_report(log)
        root_cause = str(getattr(report, "root_cause", ""))
        assert root_cause, "root_cause must not be empty for multi-error logs"
        # Root cause should reference the earliest / most fundamental error
        assert (
            "ConnectionError" in root_cause
            or "db.py" in root_cause
            or "connectionerror" in root_cause.lower()
        ), f"root_cause should reference the fundamental error, got: {root_cause!r}"

    def test_malformed_annotation_does_not_crash_parser(self):
        """Verify CILogParser handles malformed annotations without raising exceptions."""
        mod = _try_import_ci_analyzer()
        parser = mod.CILogParser()
        malformed = "::error\n::error file=\n::notannotation: some text"
        try:
            result = parser.parse(malformed)
        except Exception as exc:
            pytest.fail(
                f"CILogParser.parse raised an exception on malformed input: {exc}"
            )
        # Result must be returned gracefully (not crash)
        assert (
            result is not None
        ), "parse() must return a result even for malformed input"

    def test_each_failure_has_category_attribute(self):
        """Verify each parsed failure has a category attribute with a valid FailureCategory value."""
        mod = _try_import_ci_analyzer()
        parser = mod.CILogParser()
        log = (
            "::error file=test.py,line=1::import error\n"
            "::error file=test.py,line=2::timeout\n"
            "::error file=test.py,line=3::assertion failed"
        )
        result = parser.parse(log)
        failures = (
            getattr(result, "failures", result)
            if not isinstance(result, list)
            else result
        )
        failures = failures or []
        if not failures:
            pytest.skip("No failures parsed; cannot verify category attribute")
        for failure in failures:
            assert hasattr(
                failure, "category"
            ), f"Failure object must have 'category' attribute: {failure}"
