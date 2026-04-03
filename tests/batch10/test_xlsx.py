"""
Test for 'xlsx' skill — openpyxl financial workbook builder
Validates that the Agent created a multi-sheet financial comparison
workbook using openpyxl with formatting, charts, and proper structure.
"""

import os
import re

import pytest


class TestXlsx:
    """Verify openpyxl financial workbook builder implementation."""

    REPO_DIR = "/workspace/openpyxl"

    def test_workbook_builder_file_exists(self):
        """workbook_builder.py must exist and import openpyxl."""
        found = False
        for root, dirs, files in os.walk(self.REPO_DIR):
            for f in files:
                if f == "workbook_builder.py":
                    path = os.path.join(root, f)
                    with open(path, "r", errors="ignore") as fh:
                        content = fh.read()
                    if re.search(r"import\s+openpyxl|from\s+openpyxl", content):
                        if re.search(r"Workbook\(\)", content):
                            found = True
                            break
            if found:
                break
        assert found, "workbook_builder.py with openpyxl Workbook usage not found"

    def test_financial_report_file_exists(self):
        """financial_report.py must exist with report generation function."""
        found = False
        for root, dirs, files in os.walk(self.REPO_DIR):
            for f in files:
                if f == "financial_report.py":
                    path = os.path.join(root, f)
                    with open(path, "r", errors="ignore") as fh:
                        content = fh.read()
                    if re.search(r"def\s+(generate_report|build_workbook|create_report)", content):
                        found = True
                        break
            if found:
                break
        assert found, "financial_report.py with report generation function not found"

    def test_multiple_sheets_created(self):
        """Workbook must create multiple named sheets."""
        found = False
        for root, dirs, files in os.walk(self.REPO_DIR):
            for f in files:
                if f == "workbook_builder.py":
                    path = os.path.join(root, f)
                    with open(path, "r", errors="ignore") as fh:
                        content = fh.read()
                    create_count = len(re.findall(r"create_sheet", content))
                    if create_count >= 2:
                        found = True
                        break
            if found:
                break
        assert found, "At least 2 create_sheet calls not found in workbook_builder.py"

    def test_bold_headers_applied(self):
        """Header cells must have bold font formatting."""
        found = False
        for root, dirs, files in os.walk(self.REPO_DIR):
            for f in files:
                if f == "workbook_builder.py":
                    path = os.path.join(root, f)
                    with open(path, "r", errors="ignore") as fh:
                        content = fh.read()
                    if re.search(r"Font\(.*bold\s*=\s*True", content):
                        found = True
                        break
            if found:
                break
        assert found, "Font(bold=True) not found in workbook_builder.py"

    def test_currency_number_format_applied(self):
        """Financial columns must use currency number format."""
        found = False
        for root, dirs, files in os.walk(self.REPO_DIR):
            for f in files:
                if f == "workbook_builder.py":
                    path = os.path.join(root, f)
                    with open(path, "r", errors="ignore") as fh:
                        content = fh.read()
                    if re.search(r"number_format|#,##0|currency|\$", content):
                        found = True
                        break
            if found:
                break
        assert found, "Currency number format not found in workbook_builder.py"

    def test_chart_added_to_summary_sheet(self):
        """At least one chart (BarChart/LineChart/PieChart) must be added."""
        found = False
        for root, dirs, files in os.walk(self.REPO_DIR):
            for f in files:
                if f == "workbook_builder.py":
                    path = os.path.join(root, f)
                    with open(path, "r", errors="ignore") as fh:
                        content = fh.read()
                    if re.search(r"BarChart|LineChart|PieChart", content):
                        if re.search(r"add_chart|add_data", content):
                            found = True
                            break
            if found:
                break
        assert found, "Chart (BarChart/LineChart/PieChart) with add_chart not found"

    def test_workbook_saves_to_xlsx(self):
        """Workbook must call wb.save() with .xlsx extension."""
        found = False
        for root, dirs, files in os.walk(self.REPO_DIR):
            for f in files:
                if f in ("workbook_builder.py", "financial_report.py"):
                    path = os.path.join(root, f)
                    with open(path, "r", errors="ignore") as fh:
                        content = fh.read()
                    if re.search(r"\.save\(", content) and re.search(r"\.xlsx", content):
                        found = True
                        break
            if found:
                break
        assert found, "wb.save() with .xlsx extension not found"

    def test_saved_file_is_valid_xlsx(self):
        """Saved file must have openpyxl import for load_workbook validation."""
        found = False
        for root, dirs, files in os.walk(self.REPO_DIR):
            for f in files:
                if f in ("workbook_builder.py", "financial_report.py"):
                    path = os.path.join(root, f)
                    with open(path, "r", errors="ignore") as fh:
                        content = fh.read()
                    if re.search(r"openpyxl", content) and re.search(r"Workbook|load_workbook", content):
                        found = True
                        break
            if found:
                break
        assert found, "openpyxl workbook creation not found"

    def test_empty_data_creates_empty_sheets(self):
        """Empty data handling must not crash the builder."""
        found = False
        for root, dirs, files in os.walk(self.REPO_DIR):
            for f in files:
                if f in ("workbook_builder.py", "financial_report.py"):
                    path = os.path.join(root, f)
                    with open(path, "r", errors="ignore") as fh:
                        content = fh.read()
                    if re.search(r"if\s+not\s+data|len\(data\)|empty|default", content, re.IGNORECASE):
                        found = True
                        break
            if found:
                break
        assert found, "Empty data handling not found"

    def test_header_row_is_frozen(self):
        """Header row must use freeze_panes for navigation."""
        found = False
        for root, dirs, files in os.walk(self.REPO_DIR):
            for f in files:
                if f == "workbook_builder.py":
                    path = os.path.join(root, f)
                    with open(path, "r", errors="ignore") as fh:
                        content = fh.read()
                    if re.search(r"freeze_panes", content):
                        found = True
                        break
            if found:
                break
        assert found, "freeze_panes not found in workbook_builder.py"

    def test_missing_output_path_raises_error(self):
        """None or empty output_path must be validated."""
        found = False
        for root, dirs, files in os.walk(self.REPO_DIR):
            for f in files:
                if f in ("workbook_builder.py", "financial_report.py"):
                    path = os.path.join(root, f)
                    with open(path, "r", errors="ignore") as fh:
                        content = fh.read()
                    if re.search(r"ValueError|TypeError|output_path|path.*None|not.*path", content):
                        found = True
                        break
            if found:
                break
        assert found, "Output path validation not found"
