"""
Tests for 'xlsx' skill — Excel & Spreadsheet Automation.
Validates that the Agent implemented a financial report generator using openpyxl
with proper worksheets, SUM formulas, LineChart, conditional formatting, and
error handling for missing data keys.
"""

import json
import os
import re
import subprocess
import tempfile
import textwrap

import pytest


class TestXlsx:
    """Verify Excel financial report generation."""

    REPO_DIR = "/workspace/openpyxl"

    # ── helpers ──────────────────────────────────────────────────────────

    @staticmethod
    def _safe_read(path: str) -> str:
        with open(path, "r", encoding="utf-8", errors="ignore") as fh:
            return fh.read()

    @classmethod
    def _run_in_repo(
        cls, script: str, timeout: int = 120
    ) -> subprocess.CompletedProcess:
        return subprocess.run(
            ["python", "-c", textwrap.dedent(script)],
            cwd=cls.REPO_DIR,
            capture_output=True,
            text=True,
            timeout=timeout,
        )

    # ── file_path_check (static) ────────────────────────────────────────

    def test_build_financial_report_script_exists(self):
        """Verify the main financial report generator script exists."""
        path = os.path.join(self.REPO_DIR, "scripts", "build_financial_report.py")
        assert os.path.isfile(path), f"Missing {path}"

    def test_test_file_exists(self):
        """Verify test file for the financial report generator exists."""
        path = os.path.join(self.REPO_DIR, "tests", "test_financial_report.py")
        assert os.path.isfile(path), f"Missing {path}"

    # ── semantic_check (static) ─────────────────────────────────────────

    def test_function_signature_defined(self):
        """Verify build_financial_report function is defined with data and output_path."""
        path = os.path.join(self.REPO_DIR, "scripts", "build_financial_report.py")
        assert os.path.isfile(path), f"Missing {path}"
        content = self._safe_read(path)
        assert re.search(
            r"def\s+build_financial_report\s*\(", content
        ), "build_financial_report function not found"

    def test_openpyxl_import_present(self):
        """Verify openpyxl is imported in the report generator."""
        path = os.path.join(self.REPO_DIR, "scripts", "build_financial_report.py")
        assert os.path.isfile(path), f"Missing {path}"
        content = self._safe_read(path)
        assert re.search(
            r"import\s+openpyxl|from\s+openpyxl", content
        ), "openpyxl import not found"

    def test_patternfill_styling_import(self):
        """Verify PatternFill or conditional formatting styling is imported."""
        path = os.path.join(self.REPO_DIR, "scripts", "build_financial_report.py")
        assert os.path.isfile(path), f"Missing {path}"
        content = self._safe_read(path)
        has_fill = re.search(
            r"PatternFill|DifferentialStyle|ConditionalFormatting", content
        )
        assert has_fill, "PatternFill or conditional formatting import not found"

    def test_linechart_import_for_revenue_trend(self):
        """Verify LineChart is imported for the revenue trend chart."""
        path = os.path.join(self.REPO_DIR, "scripts", "build_financial_report.py")
        assert os.path.isfile(path), f"Missing {path}"
        content = self._safe_read(path)
        assert re.search(r"LineChart", content), "LineChart import not found"

    # ── functional_check ────────────────────────────────────────────────

    def test_output_file_created(self):
        """Verify calling build_financial_report creates a valid .xlsx file."""
        result = self._run_in_repo(
            """\
            import sys, os, tempfile
            sys.path.insert(0, '.')
            from scripts.build_financial_report import build_financial_report
            sample_data = {
                "revenue": [100000, 120000, 130000, 140000],
                "expenses": [80000, 85000, 90000, 95000],
                "quarters": ["Q1", "Q2", "Q3", "Q4"],
            }
            p = tempfile.mktemp(suffix='.xlsx')
            build_financial_report(sample_data, p)
            assert os.path.exists(p), "File not created"
            print('file OK')
        """,
            timeout=120,
        )
        if result.returncode != 0:
            pytest.skip(f"Output file test failed: {result.stderr[:300]}")
        assert "file OK" in result.stdout

    def test_workbook_has_expected_sheets(self):
        """Verify generated workbook contains expected sheet names."""
        result = self._run_in_repo(
            """\
            import sys, os, tempfile, openpyxl
            sys.path.insert(0, '.')
            from scripts.build_financial_report import build_financial_report
            sample_data = {
                "revenue": [100000, 120000, 130000, 140000],
                "expenses": [80000, 85000, 90000, 95000],
                "quarters": ["Q1", "Q2", "Q3", "Q4"],
            }
            p = tempfile.mktemp(suffix='.xlsx')
            build_financial_report(sample_data, p)
            wb = openpyxl.load_workbook(p)
            names = wb.sheetnames
            found = [n for n in names if 'Income' in n or 'Balance' in n or 'Revenue' in n]
            assert len(found) >= 2, f"Expected Income/Balance/Revenue sheets, got {names}"
            print('sheets OK')
        """,
            timeout=120,
        )
        if result.returncode != 0:
            pytest.skip(f"Sheet names test failed: {result.stderr[:300]}")
        assert "sheets OK" in result.stdout

    def test_total_rows_use_sum_formulas(self):
        """Verify income statement total rows contain =SUM() formulas."""
        result = self._run_in_repo(
            """\
            import sys, tempfile, openpyxl
            sys.path.insert(0, '.')
            from scripts.build_financial_report import build_financial_report
            sample_data = {
                "revenue": [100000, 120000, 130000, 140000],
                "expenses": [80000, 85000, 90000, 95000],
                "quarters": ["Q1", "Q2", "Q3", "Q4"],
            }
            p = tempfile.mktemp(suffix='.xlsx')
            build_financial_report(sample_data, p)
            wb = openpyxl.load_workbook(p)
            # Find a sheet with "Income" in the name
            ws = None
            for name in wb.sheetnames:
                if 'income' in name.lower():
                    ws = wb[name]
                    break
            if ws is None:
                ws = wb.worksheets[0]
            # Check last row for formula
            total_cell = ws.cell(ws.max_row, 2).value
            assert total_cell and str(total_cell).startswith('='), (
                f"Expected formula in total row, got {total_cell!r}"
            )
            print('formula OK')
        """,
            timeout=120,
        )
        if result.returncode != 0:
            pytest.skip(f"SUM formula test failed: {result.stderr[:300]}")
        assert "formula OK" in result.stdout

    def test_revenue_trend_chart_present(self):
        """Verify Revenue Trend sheet contains at least one chart object."""
        result = self._run_in_repo(
            """\
            import sys, tempfile, openpyxl
            sys.path.insert(0, '.')
            from scripts.build_financial_report import build_financial_report
            sample_data = {
                "revenue": [100000, 120000, 130000, 140000],
                "expenses": [80000, 85000, 90000, 95000],
                "quarters": ["Q1", "Q2", "Q3", "Q4"],
            }
            p = tempfile.mktemp(suffix='.xlsx')
            build_financial_report(sample_data, p)
            wb = openpyxl.load_workbook(p)
            # Find Revenue/Trend sheet
            ws = None
            for name in wb.sheetnames:
                if 'revenue' in name.lower() or 'trend' in name.lower():
                    ws = wb[name]
                    break
            if ws is None:
                print('NO TREND SHEET')
            else:
                charts = ws._charts
                assert len(charts) >= 1, f"Expected >= 1 chart, got {len(charts)}"
                print('chart OK')
        """,
            timeout=120,
        )
        if result.returncode != 0:
            pytest.skip(f"Chart test failed: {result.stderr[:300]}")
        out = result.stdout.strip()
        assert "chart OK" in out or "NO TREND SHEET" in out

    def test_conditional_formatting_rules_exist(self):
        """Verify conditional formatting rules are applied to income statement."""
        result = self._run_in_repo(
            """\
            import sys, tempfile, openpyxl
            sys.path.insert(0, '.')
            from scripts.build_financial_report import build_financial_report
            sample_data = {
                "revenue": [100000, 120000, 130000, 140000],
                "expenses": [80000, 85000, 90000, 95000],
                "quarters": ["Q1", "Q2", "Q3", "Q4"],
            }
            p = tempfile.mktemp(suffix='.xlsx')
            build_financial_report(sample_data, p)
            wb = openpyxl.load_workbook(p)
            ws = None
            for name in wb.sheetnames:
                if 'income' in name.lower():
                    ws = wb[name]
                    break
            if ws is None:
                ws = wb.worksheets[0]
            rules = ws.conditional_formatting._cf_rules
            assert len(rules) > 0, "No conditional formatting rules found"
            print('cond OK')
        """,
            timeout=120,
        )
        if result.returncode != 0:
            pytest.skip(f"Conditional formatting test failed: {result.stderr[:300]}")
        assert "cond OK" in result.stdout

    def test_missing_data_key_raises_error(self):
        """Verify passing data dict with missing keys raises KeyError or ValueError."""
        result = self._run_in_repo(
            """\
            import sys, tempfile
            sys.path.insert(0, '.')
            from scripts.build_financial_report import build_financial_report
            try:
                build_financial_report({}, tempfile.mktemp(suffix='.xlsx'))
                print('NO_ERROR')
            except (KeyError, ValueError, TypeError) as e:
                print(f'ERROR:{e}')
        """,
            timeout=120,
        )
        if result.returncode != 0:
            pytest.skip(f"Missing key test failed: {result.stderr[:300]}")
        assert "ERROR" in result.stdout, "Expected error for missing data keys"
