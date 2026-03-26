"""
Tests for dbt-transformation-patterns skill.
Validates dbt medallion architecture SQL models and YAML schemas in dbt-core repository.
"""

import os
import subprocess
import sys
import pytest

REPO_DIR = "/workspace/dbt-core"


def _path(rel: str) -> str:
    return os.path.join(REPO_DIR, rel)


def _read(rel: str) -> str:
    with open(_path(rel), encoding="utf-8", errors="ignore") as f:
        return f.read()


def _run(cmd: str, cwd: str = REPO_DIR, timeout: int = 30):
    return subprocess.run(
        cmd, shell=True, cwd=cwd, capture_output=True, text=True, timeout=timeout
    )


class TestDbtTransformationPatterns:

    # ── file_path_check ──────────────────────────────────────────────────────

    def test_staging_model_files_exist(self):
        """stg_orders.sql and stg_customers.sql must exist."""
        for rel in [
            "tests/functional/medallion/models/staging/stg_orders.sql",
            "tests/functional/medallion/models/staging/stg_customers.sql",
        ]:
            assert os.path.isfile(_path(rel)), f"{rel} not found"

    def test_intermediate_and_mart_models_exist(self):
        """int_orders.sql and fct_orders.sql must exist."""
        for rel in [
            "tests/functional/medallion/models/intermediate/int_orders.sql",
            "tests/functional/medallion/models/mart/fct_orders.sql",
        ]:
            assert os.path.isfile(_path(rel)), f"{rel} not found"

    def test_schema_yml_files_exist(self):
        """Schema YAML documentation files must exist."""
        for rel in [
            "tests/functional/medallion/models/staging/schema.yml",
            "tests/functional/medallion/models/mart/schema.yml",
        ]:
            assert os.path.isfile(_path(rel)), f"{rel} not found"

    # ── semantic_check ───────────────────────────────────────────────────────

    def test_stg_orders_references_source(self):
        """stg_orders.sql must use source() macro to reference raw.orders."""
        content = _read("tests/functional/medallion/models/staging/stg_orders.sql")
        assert (
            "source" in content.lower() and "orders" in content
        ), "stg_orders.sql must contain source() macro referencing raw.orders"

    def test_stg_customers_has_row_number_deduplication(self):
        """stg_customers.sql must use row_number() window function for deduplication."""
        content = _read("tests/functional/medallion/models/staging/stg_customers.sql")
        assert (
            "row_number" in content.lower()
        ), "stg_customers.sql must contain row_number() for deduplication"
        assert (
            "partition by" in content.lower() or "PARTITION BY" in content
        ), "stg_customers.sql must contain PARTITION BY clause"

    def test_fct_orders_uses_incremental_macro(self):
        """fct_orders.sql must use is_incremental() macro."""
        content = _read("tests/functional/medallion/models/mart/fct_orders.sql")
        assert (
            "is_incremental" in content
        ), "fct_orders.sql must contain {{ is_incremental() }} macro"

    def test_schema_yml_is_valid_yaml(self):
        """staging schema.yml must parse as valid YAML with version: 2."""
        import yaml

        content = _read("tests/functional/medallion/models/staging/schema.yml")
        data = yaml.safe_load(content)
        assert data is not None, "schema.yml parsed as empty"
        assert data.get("version") == 2, "schema.yml must declare 'version: 2'"

    # ── functional_check ─────────────────────────────────────────────────────

    def test_yaml_schema_parseable_via_python(self):
        """Python yaml.safe_load must succeed on staging schema.yml."""
        schema_path = _path("tests/functional/medallion/models/staging/schema.yml")
        if not os.path.isfile(schema_path):
            pytest.skip("staging schema.yml not found")
        result = _run(
            f"python -c \"import yaml; yaml.safe_load(open('{schema_path}'))\""
        )
        assert result.returncode == 0, f"yaml.safe_load failed: {result.stderr}"

    def test_fct_orders_has_no_select_star(self):
        """fct_orders.sql must not use SELECT * (anti-pattern in mart models)."""
        content = _read("tests/functional/medallion/models/mart/fct_orders.sql")
        import re

        assert not re.search(
            r"SELECT\s+\*", content, re.IGNORECASE
        ), "fct_orders.sql must not use SELECT * — explicit column selection required"

    def test_models_reference_upstream_via_ref_macro(self):
        """fct_orders.sql must use ref() macro for upstream model dependencies."""
        content = _read("tests/functional/medallion/models/mart/fct_orders.sql")
        assert (
            "ref(" in content
        ), "fct_orders.sql must use {{ ref('...') }} macro for upstream dependencies"

    def test_stg_orders_renames_columns_semantically(self):
        """stg_orders.sql must alias at least one column to a semantic name."""
        content = _read("tests/functional/medallion/models/staging/stg_orders.sql")
        assert (
            " AS " in content.upper() or " as " in content
        ), "stg_orders.sql must contain at least one column alias (AS customer_id, etc.)"

    def test_mart_schema_yml_defines_model_tests(self):
        """mart schema.yml must define unique and not_null dbt tests."""
        content = _read("tests/functional/medallion/models/mart/schema.yml")
        assert "unique" in content, "mart schema.yml must define 'unique' data test"
        assert "not_null" in content, "mart schema.yml must define 'not_null' data test"
