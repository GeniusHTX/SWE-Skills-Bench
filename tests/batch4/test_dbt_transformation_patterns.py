"""
Test for 'dbt-transformation-patterns' skill — dbt Transformation Patterns
Validates dbt_project.yml, staging/mart models, schema YML files,
source/ref usage, and materialization configuration in the dbt-core repo.
"""

import os
import re
import glob
import pytest

import yaml


class TestDbtTransformationPatterns:
    """Tests for dbt transformation patterns in the dbt-core repo."""

    REPO_DIR = "/workspace/dbt-core"

    def _read(self, relpath):
        path = os.path.join(self.REPO_DIR, relpath)
        with open(path, "r", errors="ignore") as f:
            return f.read()

    def _find_staging_sql(self):
        return glob.glob(
            os.path.join(self.REPO_DIR, "models", "staging", "**", "*.sql"),
            recursive=True,
        )

    def _find_mart_sql(self):
        return glob.glob(
            os.path.join(self.REPO_DIR, "models", "marts", "**", "*.sql"),
            recursive=True,
        )

    def _find_schema_ymls(self):
        return glob.glob(
            os.path.join(self.REPO_DIR, "models", "**", "*.yml"), recursive=True
        )

    # --- File Path Checks ---

    def test_dbt_project_yml_exists(self):
        """Verifies dbt_project.yml exists."""
        path = os.path.join(self.REPO_DIR, "dbt_project.yml")
        assert os.path.exists(path), f"Expected file not found: {path}"

    def test_models_staging_dir_exists(self):
        """Verifies models/staging/ directory exists."""
        path = os.path.join(self.REPO_DIR, "models", "staging")
        assert os.path.isdir(path), f"Expected directory not found: {path}"

    def test_models_marts_dir_exists(self):
        """Verifies models/marts/ directory exists."""
        path = os.path.join(self.REPO_DIR, "models", "marts")
        assert os.path.isdir(path), f"Expected directory not found: {path}"

    def test_schema_yml_exists(self):
        """Verifies at least one schema YML file exists under models."""
        matches = self._find_schema_ymls()
        assert len(matches) >= 1, "No schema .yml file found under models/"

    # --- Semantic Checks ---

    def test_sem_dbt_project_parsable(self):
        """dbt_project.yml is valid YAML with 'models' key."""
        content = self._read("dbt_project.yml")
        proj = yaml.safe_load(content)
        assert "models" in proj, "dbt_project.yml missing 'models' key"

    def test_sem_staging_sql_exist(self):
        """At least one staging SQL file exists."""
        files = self._find_staging_sql()
        assert len(files) >= 1, "No staging SQL files found"

    def test_sem_mart_sql_exist(self):
        """At least one mart SQL file exists."""
        files = self._find_mart_sql()
        assert len(files) >= 1, "No mart SQL files found"

    def test_sem_schema_yml_parsable(self):
        """All schema YML files are parsable."""
        for yf in self._find_schema_ymls():
            with open(yf, "r", errors="ignore") as f:
                data = yaml.safe_load(f.read())
            assert data is not None, f"Empty or invalid schema yml: {yf}"

    # --- Functional Checks ---

    def test_func_staging_uses_source(self):
        """All staging SQL files use source()."""
        for sf in self._find_staging_sql():
            with open(sf, "r", errors="ignore") as f:
                content = f.read()
            assert re.search(
                r"\bsource\s*\(", content
            ), f"Staging file {sf} does not use source()"

    def test_func_mart_uses_ref(self):
        """All mart SQL files use ref()."""
        for mf in self._find_mart_sql():
            with open(mf, "r", errors="ignore") as f:
                content = f.read()
            assert re.search(
                r"\bref\s*\(", content
            ), f"Mart file {mf} does not use ref()"

    def test_func_mart_no_direct_table_refs(self):
        """Mart SQL files do not directly reference tables (no FROM table without ref)."""
        for mf in self._find_mart_sql():
            with open(mf, "r", errors="ignore") as f:
                content = f.read()
            # Remove comments
            cleaned = re.sub(r"--.*$", "", content, flags=re.MULTILINE)
            cleaned = re.sub(r"/\*.*?\*/", "", cleaned, flags=re.DOTALL)
            # Find FROM/JOIN clauses that don't use ref()/source()
            raw_refs = re.findall(
                r"(?:from|join)\s+(?!.*(?:ref|source)\s*\()([a-zA-Z_]\w*\.\w+)",
                cleaned,
                re.IGNORECASE,
            )
            assert len(raw_refs) == 0, f"Mart {mf} has direct table refs: {raw_refs}"

    def test_func_mart_models_have_docs(self):
        """Schema YMLs include column definitions for mart models."""
        ymls = self._find_schema_ymls()
        mart_ymls = [y for y in ymls if "marts" in y.replace("\\", "/").lower()]
        assert len(mart_ymls) >= 1, "No schema YML in marts dir"
        for y in mart_ymls:
            with open(y, "r", errors="ignore") as f:
                data = yaml.safe_load(f.read())
            if data and "models" in data:
                for m in data["models"]:
                    assert "columns" in m, f"Model {m.get('name')} missing 'columns'"

    def test_func_mart_columns_have_tests(self):
        """Mart model columns have not_null or unique tests."""
        ymls = self._find_schema_ymls()
        mart_ymls = [y for y in ymls if "marts" in y.replace("\\", "/").lower()]
        found_test = False
        for y in mart_ymls:
            with open(y, "r", errors="ignore") as f:
                data = yaml.safe_load(f.read())
            if data and "models" in data:
                for m in data["models"]:
                    for col in m.get("columns", []):
                        tests = col.get("tests", [])
                        if any(
                            t in tests or t in str(tests)
                            for t in ("not_null", "unique")
                        ):
                            found_test = True
        assert found_test, "No not_null/unique tests found on mart columns"

    def test_func_materialization_configs(self):
        """dbt_project.yml models reference view and table materializations."""
        content = self._read("dbt_project.yml")
        proj = yaml.safe_load(content)
        models_str = str(proj.get("models", ""))
        assert "view" in models_str.lower(), "No 'view' materialization found"
        assert "table" in models_str.lower(), "No 'table' materialization found"

    def test_func_staging_without_source_fails(self):
        """A staging SQL without source() would be caught (negative test)."""
        bad_sql = "SELECT * FROM raw_table"
        assert not re.search(
            r"\bsource\s*\(", bad_sql
        ), "Bad SQL should not contain source()"

    def test_func_project_has_name(self):
        """dbt_project.yml has a 'name' key."""
        content = self._read("dbt_project.yml")
        proj = yaml.safe_load(content)
        assert "name" in proj, "dbt_project.yml missing 'name'"

    def test_func_project_has_version(self):
        """dbt_project.yml has a 'version' key."""
        content = self._read("dbt_project.yml")
        proj = yaml.safe_load(content)
        assert "version" in proj, "dbt_project.yml missing 'version'"
