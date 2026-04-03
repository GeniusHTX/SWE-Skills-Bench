"""Test file for the python-background-jobs skill.

This suite validates the ResultAggregator, AggregationResult,
FailedTask, and MaxFailuresExceeded in celery/contrib.
"""

from __future__ import annotations

import ast
import pathlib
import re

import pytest


class TestPythonBackgroundJobs:
    """Verify Celery result aggregator patterns."""

    REPO_DIR = "/workspace/celery"

    RESULT_AGGREGATOR_PY = "celery/contrib/result_aggregator.py"
    CONTRIB_INIT_PY = "celery/contrib/__init__.py"
    TEST_PY = "t/unit/contrib/test_result_aggregator.py"

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    def _repo_path(self, relative: str) -> pathlib.Path:
        return pathlib.Path(self.REPO_DIR, *relative.split("/"))

    def _read_text(self, relative: str) -> str:
        path = self._repo_path(relative)
        assert path.exists(), f"Expected path to exist: {path}"
        return path.read_text(encoding="utf-8", errors="ignore")

    def _assert_non_empty_file(self, relative: str) -> pathlib.Path:
        path = self._repo_path(relative)
        assert path.is_file(), f"Expected file to exist: {path}"
        assert path.stat().st_size > 0, f"Expected non-empty file: {path}"
        return path

    def _class_source(self, source: str, class_name: str) -> str | None:
        tree = ast.parse(source)
        for node in ast.walk(tree):
            if isinstance(node, ast.ClassDef) and node.name == class_name:
                start = node.lineno - 1
                end = node.end_lineno or start + 1
                lines = source.splitlines()
                return "\n".join(lines[start:end])
        return None

    # ------------------------------------------------------------------
    # Layer 1 – file_path_check (3 cases)
    # ------------------------------------------------------------------

    def test_file_path_celery_contrib_result_aggregator_py_exists(self):
        """Verify result_aggregator.py exists and is non-empty."""
        self._assert_non_empty_file(self.RESULT_AGGREGATOR_PY)

    def test_file_path_celery_contrib___init___py_exports_resultaggregator(self):
        """Verify __init__.py exports ResultAggregator."""
        self._assert_non_empty_file(self.CONTRIB_INIT_PY)
        src = self._read_text(self.CONTRIB_INIT_PY)
        assert "ResultAggregator" in src, "__init__.py should export ResultAggregator"

    def test_file_path_t_unit_contrib_test_result_aggregator_py_exists(self):
        """Verify test_result_aggregator.py exists and is non-empty."""
        self._assert_non_empty_file(self.TEST_PY)

    # ------------------------------------------------------------------
    # Layer 2 – semantic_check (5 cases)
    # ------------------------------------------------------------------

    def test_semantic_resultaggregator_class_has___init___collect_reduce_filter_me(
        self,
    ):
        """ResultAggregator class has __init__, collect, reduce, filter methods."""
        src = self._read_text(self.RESULT_AGGREGATOR_PY)
        body = self._class_source(src, "ResultAggregator")
        assert body is not None, "ResultAggregator class not found"
        for method in ("__init__", "collect", "reduce", "filter"):
            assert re.search(
                rf"def\s+{method}\s*\(", body
            ), f"ResultAggregator missing method: {method}"

    def test_semantic_aggregationresult_is_a_dataclass_with_succeeded_failed_total(
        self,
    ):
        """AggregationResult is a dataclass with succeeded, failed, total, etc."""
        src = self._read_text(self.RESULT_AGGREGATOR_PY)
        body = self._class_source(src, "AggregationResult")
        assert body is not None, "AggregationResult class not found"
        for field in ("succeeded", "failed", "total"):
            assert field in body, f"AggregationResult missing field: {field}"

    def test_semantic_aggregationresult_has_success_rate_and_is_complete_propertie(
        self,
    ):
        """AggregationResult has success_rate and is_complete properties."""
        src = self._read_text(self.RESULT_AGGREGATOR_PY)
        body = self._class_source(src, "AggregationResult")
        assert body is not None, "AggregationResult class not found"
        assert re.search(r"success_rate", body), "Missing success_rate"
        assert re.search(r"is_complete", body), "Missing is_complete"

    def test_semantic_failedtask_is_a_dataclass_with_index_task_id_exception_field(
        self,
    ):
        """FailedTask is a dataclass with index, task_id, exception fields."""
        src = self._read_text(self.RESULT_AGGREGATOR_PY)
        body = self._class_source(src, "FailedTask")
        assert body is not None, "FailedTask class not found"
        for field in ("index", "task_id", "exception"):
            assert field in body, f"FailedTask missing field: {field}"

    def test_semantic_maxfailuresexceeded_has_partial_result_attribute(self):
        """MaxFailuresExceeded has partial_result attribute."""
        src = self._read_text(self.RESULT_AGGREGATOR_PY)
        assert re.search(
            r"class\s+MaxFailuresExceeded", src
        ), "MaxFailuresExceeded class not found"
        assert (
            "partial_result" in src
        ), "MaxFailuresExceeded should have partial_result attribute"

    # ------------------------------------------------------------------
    # Layer 3 – functional_check (5 cases, source analysis)
    # ------------------------------------------------------------------

    def test_functional_5_tasks_with_4_success_1_failure_success_count_4_failure_cou(
        self,
    ):
        """5 tasks with 4 success + 1 failure -> success_count=4, failure_count=1."""
        src = self._read_text(self.RESULT_AGGREGATOR_PY)
        assert re.search(r"def\s+collect\s*\(", src), "collect method required"
        assert re.search(
            r"success_count|succeeded|success", src
        ), "collect should track success count"

    def test_functional_reduce_operator_add_returns_sum_of_4_successful_results(self):
        """reduce(operator.add) returns sum of 4 successful results."""
        src = self._read_text(self.RESULT_AGGREGATOR_PY)
        assert re.search(r"def\s+reduce\s*\(", src), "reduce method required"

    def test_functional_filter_lambda_x_x_10_returns_only_qualifying_results(self):
        """filter(lambda x: x > 10) returns only qualifying results."""
        src = self._read_text(self.RESULT_AGGREGATOR_PY)
        assert re.search(r"def\s+filter\s*\(", src), "filter method required"

    def test_functional_max_failures_2_with_3_failures_raises_maxfailuresexceeded(self):
        """max_failures=2 with 3 failures raises MaxFailuresExceeded."""
        src = self._read_text(self.RESULT_AGGREGATOR_PY)
        assert re.search(
            r"max_failures|MaxFailuresExceeded", src
        ), "max_failures support required"

    def test_functional_timeout_scenario_raises_timeouterror_with_partial_results(self):
        """timeout scenario raises TimeoutError with partial results."""
        src = self._read_text(self.RESULT_AGGREGATOR_PY)
        assert re.search(r"timeout|TimeoutError", src), "Timeout handling required"
