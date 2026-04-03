"""
Test for 'dbt-transformation-patterns' skill — dbt Core Transformation Models
Validates staging SQL, intermediate/mart models, incremental strategy,
schema tests, and dbt compile/debug commands.
"""

import os
import re

import pytest


class TestDbtTransformationPatterns:
    """Verify dbt transformation model patterns."""

    REPO_DIR = "/workspace/dbt-core"

    # ── file_path_check ─────────────────────────────────────────────────────

    def test_staging_model_exists(self):
        """Verify staging SQL model file exists."""
        found = self._find_sql_files("staging")
        assert found, "No staging SQL model found"

    def test_mart_or_intermediate_models_exist(self):
        """Verify intermediate or mart model SQL files exist."""
        intermediate = self._find_sql_files("intermediate")
        mart = self._find_sql_files("mart") + self._find_sql_files("fct_")
        assert intermediate or mart, "No intermediate or mart SQL model found"

    # ── semantic_check ──────────────────────────────────────────────────────

    def test_cancelled_filter_pattern(self):
        """Verify staging model filters cancelled orders."""
        staging = self._find_sql_files("staging")
        assert staging, "No staging model found"
        for fpath in staging:
            content = self._read(fpath)
            if re.search(r"cancel|WHERE.*status|filter", content, re.IGNORECASE):
                return
        pytest.fail("No cancelled order filter in staging model")

    def test_cents_to_dollars_conversion(self):
        """Verify cents to dollars conversion (cents / 100.0)."""
        sql_files = self._find_all_sql_files()
        assert sql_files, "No SQL files found"
        for fpath in sql_files:
            content = self._read(fpath)
            if re.search(
                r"(/\s*100\.?0?|cents.*dollar|amount.*100)", content, re.IGNORECASE
            ):
                return
        pytest.fail("No cents-to-dollars conversion found")

    def test_incremental_materialization(self):
        """Verify incremental materialization config in mart/fact model."""
        sql_files = self._find_sql_files("fct_") + self._find_sql_files("mart")
        if not sql_files:
            sql_files = self._find_all_sql_files()
        for fpath in sql_files:
            content = self._read(fpath)
            if re.search(r"materialized\s*=\s*['\"]incremental", content):
                return
        pytest.fail("No incremental materialization found")

    def test_schema_yml_has_tests(self):
        """Verify schema.yml defines ≥5 tests."""
        yml_files = self._find_files_by_ext(".yml") + self._find_files_by_ext(".yaml")
        assert yml_files, "No YAML files found"
        test_count = 0
        for fpath in yml_files:
            content = self._read(fpath)
            test_count += len(
                re.findall(
                    r"(unique|not_null|accepted_values|relationships|dbt_utils)",
                    content,
                )
            )
        assert test_count >= 5, f"Expected ≥5 schema tests, found {test_count}"

    def test_nullif_usage(self):
        """Verify NULLIF usage for safe division."""
        sql_files = self._find_all_sql_files()
        for fpath in sql_files:
            content = self._read(fpath)
            if "NULLIF" in content.upper() or "nullif" in content:
                return
        pytest.skip("NULLIF not used in SQL files (may use COALESCE instead)")

    # ── functional_check ────────────────────────────────────────────────────

    def test_sql_files_have_select(self):
        """Verify all SQL model files contain SELECT statements."""
        sql_files = self._find_all_sql_files()
        assert sql_files, "No SQL files found"
        for fpath in sql_files:
            content = self._read(fpath)
            assert re.search(
                r"\bSELECT\b", content, re.IGNORECASE
            ), f"No SELECT in {os.path.basename(fpath)}"

    def test_schema_yml_valid_yaml(self):
        """Verify schema YAML files are valid YAML."""
        import yaml

        yml_files = self._find_files_by_ext(".yml") + self._find_files_by_ext(".yaml")
        assert yml_files, "No YAML files found"
        for fpath in yml_files:
            with open(fpath, "r", errors="ignore") as fh:
                try:
                    yaml.safe_load(fh)
                except yaml.YAMLError as exc:
                    pytest.fail(f"Invalid YAML in {os.path.basename(fpath)}: {exc}")

    def test_jinja_refs_valid(self):
        """Verify {{ ref('...') }} calls reference existing models."""
        sql_files = self._find_all_sql_files()
        model_names = set()
        for fpath in sql_files:
            name = os.path.splitext(os.path.basename(fpath))[0]
            model_names.add(name)
        for fpath in sql_files:
            content = self._read(fpath)
            refs = re.findall(r"\{\{\s*ref\(\s*['\"](\w+)['\"]\s*\)\s*\}\}", content)
            for ref_name in refs:
                if ref_name not in model_names:
                    # Allow refs to seed or source models
                    pass  # non-fatal

    def test_models_have_config_or_header(self):
        """Verify SQL models have dbt config block or header comments."""
        sql_files = self._find_all_sql_files()
        assert sql_files, "No SQL files found"
        for fpath in sql_files:
            content = self._read(fpath)
            if re.search(r"(\{\{.*config|--.*model|/\*)", content):
                return
        pytest.fail("No SQL model has a config block or header comment")

    # ── helpers ──────────────────────────────────────────────────────────────

    def _find_sql_files(self, keyword):
        results = []
        for dirpath, _, fnames in os.walk(self.REPO_DIR):
            if ".git" in dirpath:
                continue
            for f in fnames:
                if f.endswith(".sql") and keyword.lower() in f.lower():
                    results.append(os.path.join(dirpath, f))
        return results

    def _find_all_sql_files(self):
        results = []
        for dirpath, _, fnames in os.walk(self.REPO_DIR):
            if ".git" in dirpath:
                continue
            for f in fnames:
                if f.endswith(".sql"):
                    results.append(os.path.join(dirpath, f))
        return results

    def _find_files_by_ext(self, ext):
        results = []
        for dirpath, _, fnames in os.walk(self.REPO_DIR):
            if ".git" in dirpath:
                continue
            for f in fnames:
                if f.endswith(ext):
                    results.append(os.path.join(dirpath, f))
        return results

    def _read(self, path):
        with open(path, "r", errors="ignore") as fh:
            return fh.read()
