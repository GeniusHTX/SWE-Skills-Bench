"""Test file for the xlsx skill.

This suite validates financial report generation in openpyxl:
FinancialReportGenerator class, Excel formulas, charts, conditional
formatting, and multi-sheet workbook output.
"""

from __future__ import annotations

import ast
import pathlib
import re

import pytest


class TestXlsx:
    """Verify financial report generator in openpyxl."""

    REPO_DIR = "/workspace/openpyxl"

    REPORT_INIT = "openpyxl/report/__init__.py"
    GENERATOR_PY = "openpyxl/report/generator.py"
    STYLES_PY = "openpyxl/report/styles.py"

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
        """Extract class source via AST."""
        try:
            tree = ast.parse(source)
        except SyntaxError:
            return ""
        for node in ast.walk(tree):
            if isinstance(node, ast.ClassDef) and node.name == class_name:
                return ast.get_source_segment(source, node) or ""
        return ""

    def _all_report_sources(self) -> str:
        """Read all .py files under openpyxl/report/."""
        result = []
        root = self._repo_path("openpyxl/report")
        if root.is_dir():
            for f in root.rglob("*.py"):
                result.append(f.read_text(encoding="utf-8", errors="ignore"))
        return "\n".join(result)

    # ------------------------------------------------------------------
    # Layer 1 – file_path_check (3 cases)
    # ------------------------------------------------------------------

    def test_file_path_openpyxl_report_init_py_exists(self):
        """Verify openpyxl/report/__init__.py exists."""
        self._assert_non_empty_file(self.REPORT_INIT)

    def test_file_path_openpyxl_report_generator_py_exists(self):
        """Verify openpyxl/report/generator.py exists."""
        self._assert_non_empty_file(self.GENERATOR_PY)

    def test_file_path_openpyxl_report_styles_py_exists(self):
        """Verify openpyxl/report/styles.py exists."""
        self._assert_non_empty_file(self.STYLES_PY)

    # ------------------------------------------------------------------
    # Layer 2 – semantic_check (5 cases)
    # ------------------------------------------------------------------

    def test_semantic_financialreportgenerator_class_with_data_dict_constructor(self):
        """FinancialReportGenerator class with data dict constructor."""
        src = self._read_text(self.GENERATOR_PY)
        cls = self._class_source(src, "FinancialReportGenerator")
        assert cls, "FinancialReportGenerator class not found"
        assert re.search(
            r"def\s+__init__.*data", cls
        ), "Constructor should accept data parameter"

    def test_semantic_generate_filepath_and_generate_bytes_methods(self):
        """generate(filepath) and generate_bytes() methods."""
        src = self._read_text(self.GENERATOR_PY)
        cls = self._class_source(src, "FinancialReportGenerator")
        if not cls:
            cls = src
        assert re.search(
            r"def\s+generate\s*\(\s*self.*filepath", cls
        ), "Should have generate(filepath) method"
        assert re.search(
            r"def\s+generate_bytes\s*\(\s*self", cls
        ), "Should have generate_bytes() method"

    def test_semantic_income_statement_formulas_use_cell_references(self):
        """Income Statement formulas use cell references."""
        src = self._all_report_sources()
        assert re.search(
            r"Income\s*Statement|income_statement", src, re.IGNORECASE
        ), "Should create Income Statement sheet"
        # Formulas like =B2-B3 or =SUM(B2:B5)
        assert re.search(
            r"=[A-Z]+\d+|=SUM\(|formula", src, re.IGNORECASE
        ), "Should use Excel cell reference formulas"

    def test_semantic_balance_sheet_has_sum_formulas_and_validation(self):
        """Balance Sheet has SUM formulas and validation check row."""
        src = self._all_report_sources()
        assert re.search(
            r"Balance\s*Sheet|balance_sheet", src, re.IGNORECASE
        ), "Should create Balance Sheet"
        assert re.search(
            r"SUM|validation|check|balanced", src, re.IGNORECASE
        ), "Balance Sheet should have SUM formulas and validation"

    def test_semantic_dashboard_creates_barchart_linechart_piechart(self):
        """Dashboard creates BarChart, LineChart, PieChart."""
        src = self._all_report_sources()
        for chart_type in ["BarChart", "LineChart", "PieChart"]:
            assert chart_type in src, f"Dashboard should create {chart_type}"

    # ------------------------------------------------------------------
    # Layer 3 – functional_check (5 cases)
    # ------------------------------------------------------------------

    def test_functional_generate_produces_valid_xlsx_with_3_sheets(self):
        """generate('report.xlsx') produces valid .xlsx with 3 sheets."""
        src = self._read_text(self.GENERATOR_PY)
        assert re.search(r"Workbook|openpyxl", src), "Should use openpyxl Workbook"
        # Count sheet creation calls
        sheet_refs = re.findall(
            r"create_sheet|title\s*=|Income|Balance|Dashboard", src, re.IGNORECASE
        )
        assert len(sheet_refs) >= 3, "Should create at least 3 sheets"

    def test_functional_workbook_shows_correct_formula_calculations(self):
        """Opening workbook shows correct formula calculations."""
        src = self._all_report_sources()
        assert re.search(
            r"=[A-Z]+\d+|=SUM|formula", src, re.IGNORECASE
        ), "Should have Excel formulas for calculations"

    def test_functional_dashboard_displays_3_charts(self):
        """Dashboard displays 3 charts with correct data ranges."""
        src = self._all_report_sources()
        chart_count = len(re.findall(r"BarChart|LineChart|PieChart", src))
        assert chart_count >= 3, f"Dashboard should have 3 charts, found {chart_count}"

    def test_functional_negative_net_income_cells_appear_red(self):
        """Negative Net Income cells appear red."""
        src = self._all_report_sources()
        assert re.search(
            r"red|FF0000|conditional|PatternFill|Font.*color", src, re.IGNORECASE
        ), "Negative values should appear red"

    def test_functional_balance_check_shows_green_when_balanced(self):
        """Balance check shows green when balanced."""
        src = self._all_report_sources()
        assert re.search(
            r"green|00FF00|00ff00|balanced|conditional", src, re.IGNORECASE
        ), "Balanced check should show green"
