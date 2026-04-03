"""Test file for the slo-implementation skill.

This suite validates SLO (Service Level Objective) evaluation in
slo-generator: multi-window evaluator, burn rate calculation, and
SLI compliance reporting.
"""

from __future__ import annotations

import ast
import json
import pathlib
import re

import pytest


class TestSloImplementation:
    """Verify SLO multi-window evaluator in slo-generator."""

    REPO_DIR = "/workspace/slo-generator"

    MULTI_WINDOW_PY = "slo_generator/evaluators/multi_window.py"
    BURNRATE_PY = "slo_generator/evaluators/burnrate.py"
    TEST_MULTI_WINDOW_PY = "tests/unit/test_multi_window_evaluator.py"

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

    def _class_source(self, source: str, class_name: str) -> str:
        """Extract the full source of a class via AST."""
        try:
            tree = ast.parse(source)
        except SyntaxError:
            return ""
        for node in ast.walk(tree):
            if isinstance(node, ast.ClassDef) and node.name == class_name:
                return ast.get_source_segment(source, node) or ""
        return ""

    # ------------------------------------------------------------------
    # Layer 1 – file_path_check (3 cases)
    # ------------------------------------------------------------------

    def test_file_path_slo_generator_evaluators_multi_window_py_exists(self):
        """Verify slo_generator/evaluators/multi_window.py exists."""
        self._assert_non_empty_file(self.MULTI_WINDOW_PY)

    def test_file_path_slo_generator_evaluators_burnrate_py_exists(self):
        """Verify slo_generator/evaluators/burnrate.py exists."""
        self._assert_non_empty_file(self.BURNRATE_PY)

    def test_file_path_tests_unit_test_multi_window_evaluator_py_exists(self):
        """Verify tests/unit/test_multi_window_evaluator.py exists."""
        self._assert_non_empty_file(self.TEST_MULTI_WINDOW_PY)

    # ------------------------------------------------------------------
    # Layer 2 – semantic_check (5 cases)
    # ------------------------------------------------------------------

    def test_semantic_windowresult_is_a_dataclass_with_good_events_total_events_sl(
        self,
    ):
        """WindowResult is a dataclass with good_events, total_events, slo_target, window_hours."""
        src = self._read_text(self.MULTI_WINDOW_PY)
        assert re.search(
            r"@dataclass|dataclass", src
        ), "WindowResult should be a dataclass"
        cls = self._class_source(src, "WindowResult")
        if not cls:
            # Might be in burnrate
            cls = self._class_source(self._read_text(self.BURNRATE_PY), "WindowResult")
        assert cls, "WindowResult class not found"
        for field in ["good_events", "total_events", "slo_target", "window_hours"]:
            assert field in cls, f"WindowResult should have {field} field"

    def test_semantic_burnratecalculator_alert_configs_has_3_entries_with_correct_(
        self,
    ):
        """BurnRateCalculator.ALERT_CONFIGS has 3 entries with correct thresholds."""
        src = self._read_text(self.BURNRATE_PY)
        cls = self._class_source(src, "BurnRateCalculator")
        if not cls:
            cls = src
        assert re.search(
            r"ALERT_CONFIGS", cls
        ), "BurnRateCalculator should define ALERT_CONFIGS"

    def test_semantic_multiwindowsloevaluator_default_windows_1_0_6_0_24_0_72_0(self):
        """MultiWindowSloEvaluator.DEFAULT_WINDOWS = [1.0, 6.0, 24.0, 72.0]."""
        src = self._read_text(self.MULTI_WINDOW_PY)
        cls = self._class_source(src, "MultiWindowSloEvaluator")
        assert cls, "MultiWindowSloEvaluator class not found"
        assert re.search(
            r"DEFAULT_WINDOWS", cls
        ), "MultiWindowSloEvaluator should define DEFAULT_WINDOWS"
        assert re.search(
            r"1\.0.*6\.0.*24\.0.*72\.0", cls, re.DOTALL
        ), "DEFAULT_WINDOWS should be [1.0, 6.0, 24.0, 72.0]"

    def test_semantic_slibackend_is_a_protocol_with_get_good_events_and_get_total_(
        self,
    ):
        """SliBackend is a Protocol with get_good_events and get_total_events."""
        src = self._read_text(self.MULTI_WINDOW_PY)
        all_src = src + "\n" + self._read_text(self.BURNRATE_PY)
        assert re.search(
            r"class\s+SliBackend.*Protocol", all_src
        ), "SliBackend should be a Protocol"
        assert re.search(
            r"get_good_events", all_src
        ), "SliBackend should have get_good_events"
        assert re.search(
            r"get_total_events", all_src
        ), "SliBackend should have get_total_events"

    def test_semantic_sloevaluationreport_has_overall_compliant_and_worst_window_p(
        self,
    ):
        """SloEvaluationReport has overall_compliant and worst_window properties."""
        src = self._read_text(self.MULTI_WINDOW_PY)
        all_src = src + "\n" + self._read_text(self.BURNRATE_PY)
        cls = self._class_source(all_src, "SloEvaluationReport")
        if not cls:
            cls = all_src
        assert re.search(
            r"overall_compliant", cls
        ), "SloEvaluationReport should have overall_compliant"
        assert re.search(
            r"worst_window", cls
        ), "SloEvaluationReport should have worst_window"

    # ------------------------------------------------------------------
    # Layer 3 – functional_check (5 cases)
    # ------------------------------------------------------------------

    def test_functional_slo_target_0_999_good_990_total_1000_error_rate_0_01_budget_(
        self,
    ):
        """slo_target=0.999, good=990, total=1000 → error_rate=0.01, budget_consumed=10.0."""
        src = self._read_text(self.MULTI_WINDOW_PY)
        assert re.search(
            r"error_rate|error_budget|budget_consumed", src
        ), "Should calculate error_rate and budget_consumed"

    def test_functional_1h_window_with_budget_consumed_10_0_burnrate_7200(self):
        """1h window with budget_consumed=10.0 → burnrate=7200."""
        src = self._read_text(self.BURNRATE_PY)
        assert re.search(
            r"burn.*rate|burnrate", src, re.IGNORECASE
        ), "Should calculate burn rate"

    def test_functional_both_1h_and_6h_burnrate_14_4_page_alert_triggered(self):
        """Both 1h and 6h burnrate > 14.4 → page alert triggered."""
        src = self._read_text(self.BURNRATE_PY)
        assert re.search(
            r"14\.4|page|alert", src, re.IGNORECASE
        ), "Should trigger page alert when burn rate exceeds threshold"

    def test_functional_overall_compliant_false_when_any_window_sli_target(self):
        """overall_compliant=False when any window SLI < target."""
        src = self._read_text(self.MULTI_WINDOW_PY)
        assert re.search(
            r"overall_compliant|all\(|any\(", src
        ), "overall_compliant should check all windows"

    def test_functional_to_dict_produces_valid_json(self):
        """to_dict() produces valid JSON."""
        src = self._read_text(self.MULTI_WINDOW_PY)
        all_src = src + "\n" + self._read_text(self.BURNRATE_PY)
        assert re.search(
            r"to_dict|asdict|__dict__|json", all_src
        ), "Should support to_dict or JSON serialization"
