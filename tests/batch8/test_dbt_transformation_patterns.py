"""
Test for 'dbt-transformation-patterns' skill — dbt Staging + Marts Models
Validates that the Agent created dbt SQL models with ROW_NUMBER deduplication,
incremental strategy, ref() dependencies, schema tests, and source freshness.
"""

import os
import re
import subprocess

import pytest


class TestDbtTransformationPatterns:
    """Verify dbt transformation pattern implementation."""

    REPO_DIR = "/workspace/dbt-core"

    @staticmethod
    def _read(path: str) -> str:
        try:
            with open(path, "r", errors="ignore") as fh:
                return fh.read()
        except OSError:
            return ""

    # ── file_path_check ─────────────────────────────────────────────

    def test_staging_models_exist(self):
        """Verify stg_orders.sql and stg_customers.sql staging model files exist."""
        for rel in ("models/staging/stg_orders.sql",
                     "models/staging/stg_customers.sql"):
            path = os.path.join(self.REPO_DIR, rel)
            assert os.path.isfile(path), f"Missing: {rel}"

    def test_marts_and_schema_files_exist(self):
        """Verify fct_revenue.sql and schema YAML files exist."""
        for rel in ("models/marts/fct_revenue.sql",
                     "models/staging/schema.yml",
                     "models/marts/schema.yml"):
            path = os.path.join(self.REPO_DIR, rel)
            assert os.path.isfile(path), f"Missing: {rel}"

    def test_sources_yml_exists(self):
        """Verify models/sources.yml exists for raw source definitions."""
        path = os.path.join(self.REPO_DIR, "models/sources.yml")
        assert os.path.isfile(path), "models/sources.yml missing"

    # ── semantic_check ──────────────────────────────────────────────

    def test_row_number_deduplication_in_stg_orders(self):
        """Verify stg_orders.sql uses ROW_NUMBER() OVER (PARTITION BY order_id) for deduplication."""
        content = self._read(os.path.join(self.REPO_DIR, "models/staging/stg_orders.sql"))
        assert content, "stg_orders.sql is empty or unreadable"
        found = any(p in content for p in ("ROW_NUMBER()", "QUALIFY", "PARTITION BY order_id"))
        assert found, "No ROW_NUMBER deduplication pattern found in stg_orders.sql"

    def test_is_incremental_in_fct_revenue(self):
        """Verify fct_revenue.sql contains is_incremental() macro block."""
        content = self._read(os.path.join(self.REPO_DIR, "models/marts/fct_revenue.sql"))
        assert content, "fct_revenue.sql is empty or unreadable"
        assert "is_incremental()" in content, "is_incremental() macro not found"

    def test_ref_dependencies_in_fct_revenue(self):
        """Verify fct_revenue.sql uses ref('stg_orders') and ref('stg_customers')."""
        content = self._read(os.path.join(self.REPO_DIR, "models/marts/fct_revenue.sql"))
        assert content, "fct_revenue.sql is empty or unreadable"
        assert "ref('stg_orders')" in content, "ref('stg_orders') not found"
        assert "ref('stg_customers')" in content, "ref('stg_customers') not found"

    def test_not_null_unique_tests_in_schema_yml(self):
        """Verify schema.yml defines not_null and unique tests on order_id column."""
        content = self._read(os.path.join(self.REPO_DIR, "models/staging/schema.yml"))
        assert content, "schema.yml is empty or unreadable"
        for kw in ("not_null", "unique", "order_id"):
            assert kw in content, f"'{kw}' not found in staging schema.yml"

    def test_freshness_config_in_sources_yml(self):
        """Verify sources.yml contains warn_after and error_after freshness configuration."""
        content = self._read(os.path.join(self.REPO_DIR, "models/sources.yml"))
        assert content, "sources.yml is empty or unreadable"
        assert "warn_after" in content, "warn_after not found in sources.yml"
        assert "error_after" in content, "error_after not found in sources.yml"

    # ── functional_check (command) ──────────────────────────────────

    def _skip_unless_dbt(self):
        if not os.path.isdir(self.REPO_DIR):
            pytest.skip("Repo dir does not exist")
        result = subprocess.run(
            ["dbt", "--version"], capture_output=True, text=True, timeout=15)
        if result.returncode != 0:
            pytest.skip("dbt CLI not available")

    def test_dbt_compile_stg_orders(self):
        """dbt compile --select stg_orders exits 0 (valid SQL syntax and references)."""
        self._skip_unless_dbt()
        result = subprocess.run(
            ["dbt", "compile", "--select", "stg_orders"],
            capture_output=True, text=True, cwd=self.REPO_DIR, timeout=120,
        )
        assert result.returncode == 0, f"dbt compile failed: {result.stderr}"

    def test_dbt_compile_fct_revenue(self):
        """dbt compile --select fct_revenue exits 0."""
        self._skip_unless_dbt()
        result = subprocess.run(
            ["dbt", "compile", "--select", "fct_revenue"],
            capture_output=True, text=True, cwd=self.REPO_DIR, timeout=120,
        )
        assert result.returncode == 0, f"dbt compile failed: {result.stderr}"
