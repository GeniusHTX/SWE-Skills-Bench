"""
Test for 'dbt-transformation-patterns' skill — dbt Incremental Merge & Schema Evolution
Validates that the Agent created incremental_merge.py with merge logic using unique key,
and schema_evolution.py with on_schema_change handling (ignore, append_new_columns, fail).
Both must be valid Python.
"""

import os
import re
import subprocess

import pytest


class TestDbtTransformationPatterns:
    """Verify dbt incremental merge and schema evolution implementations."""

    REPO_DIR = "/workspace/dbt-core"

    def _read(self, *parts):
        fpath = os.path.join(self.REPO_DIR, *parts)
        assert os.path.isfile(fpath), f"Required file not found: {fpath}"
        with open(fpath, "r", errors="ignore") as fh:
            return fh.read()

    # ------------------------------------------------------------------
    # L1: File existence
    # ------------------------------------------------------------------

    def test_incremental_merge_exists(self):
        """incremental_merge.py must exist."""
        assert os.path.isfile(
            os.path.join(
                self.REPO_DIR, "core", "dbt", "materializations", "incremental_merge.py"
            )
        )

    def test_schema_evolution_exists(self):
        """schema_evolution.py must exist."""
        assert os.path.isfile(
            os.path.join(
                self.REPO_DIR, "core", "dbt", "materializations", "schema_evolution.py"
            )
        )

    # ------------------------------------------------------------------
    # L1: Valid Python
    # ------------------------------------------------------------------

    def test_incremental_merge_valid_python(self):
        """incremental_merge.py must be syntactically valid Python."""
        result = subprocess.run(
            [
                "python3",
                "-m",
                "py_compile",
                "core/dbt/materializations/incremental_merge.py",
            ],
            cwd=self.REPO_DIR,
            capture_output=True,
            text=True,
            timeout=30,
        )
        assert result.returncode == 0, f"Syntax error:\n{result.stderr}"

    def test_schema_evolution_valid_python(self):
        """schema_evolution.py must be syntactically valid Python."""
        result = subprocess.run(
            [
                "python3",
                "-m",
                "py_compile",
                "core/dbt/materializations/schema_evolution.py",
            ],
            cwd=self.REPO_DIR,
            capture_output=True,
            text=True,
            timeout=30,
        )
        assert result.returncode == 0, f"Syntax error:\n{result.stderr}"

    # ------------------------------------------------------------------
    # L2: Incremental merge — unique key
    # ------------------------------------------------------------------

    def test_merge_uses_unique_key(self):
        """incremental_merge.py must implement merge logic with unique_key."""
        content = self._read("core", "dbt", "materializations", "incremental_merge.py")
        assert re.search(
            r"unique_key", content
        ), "No unique_key reference in incremental_merge.py"

    def test_merge_has_merge_sql(self):
        """incremental_merge.py must build MERGE or INSERT/UPDATE SQL."""
        content = self._read("core", "dbt", "materializations", "incremental_merge.py")
        patterns = [
            r"MERGE\s+INTO",
            r"merge",
            r"INSERT.*ON\s+CONFLICT",
            r"upsert",
            r"insert.*update",
        ]
        assert any(
            re.search(p, content, re.IGNORECASE) for p in patterns
        ), "No MERGE/upsert SQL generation found"

    def test_merge_handles_source_and_target(self):
        """incremental_merge.py must reference source and target relations."""
        content = self._read("core", "dbt", "materializations", "incremental_merge.py")
        has_source = re.search(r"(source|src|tmp|staging)", content, re.IGNORECASE)
        has_target = re.search(
            r"(target|dest|destination|existing)", content, re.IGNORECASE
        )
        assert (
            has_source and has_target
        ), "Must reference both source and target relations"

    def test_merge_has_function_or_class(self):
        """incremental_merge.py should define functions or a class."""
        content = self._read("core", "dbt", "materializations", "incremental_merge.py")
        assert re.search(
            r"(def\s+\w+|class\s+\w+)", content
        ), "No function or class definition found"

    # ------------------------------------------------------------------
    # L2: Schema evolution — on_schema_change strategies
    # ------------------------------------------------------------------

    def test_schema_evolution_ignore(self):
        """schema_evolution.py must handle on_schema_change='ignore'."""
        content = self._read("core", "dbt", "materializations", "schema_evolution.py")
        assert re.search(
            r"ignore", content, re.IGNORECASE
        ), "Missing 'ignore' schema change strategy"

    def test_schema_evolution_append_new_columns(self):
        """schema_evolution.py must handle on_schema_change='append_new_columns'."""
        content = self._read("core", "dbt", "materializations", "schema_evolution.py")
        assert re.search(
            r"append_new_columns", content, re.IGNORECASE
        ), "Missing 'append_new_columns' schema change strategy"

    def test_schema_evolution_fail(self):
        """schema_evolution.py must handle on_schema_change='fail'."""
        content = self._read("core", "dbt", "materializations", "schema_evolution.py")
        assert re.search(
            r"fail", content, re.IGNORECASE
        ), "Missing 'fail' schema change strategy"

    def test_schema_evolution_on_schema_change_param(self):
        """schema_evolution.py must reference on_schema_change parameter."""
        content = self._read("core", "dbt", "materializations", "schema_evolution.py")
        assert re.search(
            r"on_schema_change", content
        ), "No on_schema_change parameter reference found"

    # ------------------------------------------------------------------
    # L2: Schema evolution quality
    # ------------------------------------------------------------------

    def test_schema_evolution_column_handling(self):
        """Schema evolution should manipulate columns (add/alter/compare)."""
        content = self._read("core", "dbt", "materializations", "schema_evolution.py")
        patterns = [
            r"column",
            r"ALTER\s+TABLE",
            r"ADD\s+COLUMN",
            r"schema.*diff",
        ]
        assert any(
            re.search(p, content, re.IGNORECASE) for p in patterns
        ), "No column manipulation logic found"

    def test_schema_evolution_has_function_or_class(self):
        """schema_evolution.py should define functions or a class."""
        content = self._read("core", "dbt", "materializations", "schema_evolution.py")
        assert re.search(
            r"(def\s+\w+|class\s+\w+)", content
        ), "No function or class definition found"
