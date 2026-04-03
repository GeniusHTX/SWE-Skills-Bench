"""
Test for 'dbt-transformation-patterns' skill — dbt Project Patterns
Validates dbt_project.yml, sources.yml, staging SQL models,
source/ref macros, schema tests, and YAML parsing.
"""

import glob
import os
import re

import pytest


class TestDbtTransformationPatterns:
    """Verify dbt project: YAML configs, SQL macros, schema tests."""

    REPO_DIR = "/workspace/dbt-core"

    # ── helpers ──────────────────────────────────────────────────────────

    @staticmethod
    def _read_file(path: str) -> str:
        try:
            with open(path, "r", errors="ignore") as fh:
                return fh.read()
        except OSError:
            return ""

    def _root(self, *parts) -> str:
        return os.path.join(self.REPO_DIR, *parts)

    # ── file_path_check ──────────────────────────────────────────────────

    def test_dbt_project_yml_exists(self):
        """dbt_project.yml must exist at repo root."""
        path = self._root("dbt_project.yml")
        assert os.path.isfile(path), "dbt_project.yml not found"
        assert os.path.getsize(path) > 0

    def test_sources_yml_exists(self):
        """models/sources.yml must exist."""
        path = self._root("models", "sources.yml")
        assert os.path.isfile(path), "models/sources.yml not found"

    def test_staging_sql_files_exist(self):
        """At least one stg_*.sql must exist in models/staging/."""
        pattern = self._root("models", "staging", "stg_*.sql")
        assert glob.glob(pattern), "No stg_*.sql in models/staging/"

    # ── semantic_check ───────────────────────────────────────────────────

    def test_dbt_project_yml_valid_yaml(self):
        """dbt_project.yml must parse with name and version keys."""
        try:
            import yaml
        except ImportError:
            pytest.skip("pyyaml not available")
        path = self._root("dbt_project.yml")
        with open(path) as f:
            config = yaml.safe_load(f)
        assert isinstance(config, dict)
        assert config.get("name"), "dbt_project.yml missing 'name'"
        assert "version" in config

    def test_staging_models_use_source_macro(self):
        """All stg_*.sql files must use {{ source() }} macro."""
        files = glob.glob(self._root("models", "staging", "stg_*.sql"))
        if not files:
            pytest.skip("No staging SQL files")
        for f in files:
            content = self._read_file(f)
            assert "{{ source(" in content, f"Missing source macro in {f}"

    def test_downstream_models_use_ref_macro(self):
        """Non-staging models must use {{ ref() }} macro."""
        dirs = [
            self._root("models", "marts"),
            self._root("models", "intermediate"),
        ]
        for d in dirs:
            if not os.path.isdir(d):
                continue
            for f in glob.glob(os.path.join(d, "*.sql")):
                content = self._read_file(f)
                assert "{{ ref(" in content, f"Missing ref macro in {f}"

    def test_schema_yml_has_not_null_and_unique_tests(self):
        """Schema YAML files must define not_null and unique tests."""
        found_not_null = False
        found_unique = False
        for root, _, files in os.walk(self._root("models")):
            for fname in files:
                if fname.endswith(".yml") or fname.endswith(".yaml"):
                    content = self._read_file(os.path.join(root, fname))
                    if "not_null" in content:
                        found_not_null = True
                    if "unique" in content:
                        found_unique = True
        assert found_not_null, "not_null test not found in schema YAML"
        assert found_unique, "unique test not found in schema YAML"

    def test_macros_directory_exists(self):
        """macros/ must have at least one .sql with {% macro %}."""
        macros_dir = self._root("macros")
        if not os.path.isdir(macros_dir):
            pytest.skip("macros/ not found")
        files = glob.glob(os.path.join(macros_dir, "**", "*.sql"), recursive=True)
        found = any("{% macro" in self._read_file(f) for f in files)
        assert found, "No {% macro %} definition in macros/"

    # ── functional_check ─────────────────────────────────────────────────

    def test_sources_yml_has_sources_key(self):
        """sources.yml must parse with non-empty 'sources' list."""
        try:
            import yaml
        except ImportError:
            pytest.skip("pyyaml not available")
        path = self._root("models", "sources.yml")
        with open(path) as f:
            config = yaml.safe_load(f)
        sources = config.get("sources", [])
        assert isinstance(sources, list) and len(sources) >= 1
        assert "name" in sources[0]

    def test_dbt_project_declares_model_paths(self):
        """dbt_project.yml must include 'models' in model-paths."""
        try:
            import yaml
        except ImportError:
            pytest.skip("pyyaml not available")
        path = self._root("dbt_project.yml")
        with open(path) as f:
            config = yaml.safe_load(f)
        paths = config.get("model-paths", config.get("source-paths", []))
        assert "models" in paths, "'models' not in model-paths"

    def test_no_raw_table_references_in_staging(self):
        """Staging SQL must not have raw FROM schema.table references."""
        files = glob.glob(self._root("models", "staging", "stg_*.sql"))
        for f in files:
            content = self._read_file(f)
            # Remove Jinja macro blocks to avoid false positives
            cleaned = re.sub(r"\{\{.*?\}\}", "", content, flags=re.DOTALL)
            match = re.search(r"FROM\s+[a-z_]+\.[a-z_]+", cleaned, re.IGNORECASE)
            assert match is None, f"Raw table reference in {f}: {match.group()}"

    def test_schema_yml_version_is_integer_2(self):
        """schema.yml version field must be integer 2."""
        try:
            import yaml
        except ImportError:
            pytest.skip("pyyaml not available")
        path = self._root("models", "schema.yml")
        if not os.path.isfile(path):
            pytest.skip("models/schema.yml not found")
        with open(path) as f:
            config = yaml.safe_load(f)
        assert config.get("version") == 2, "schema.yml version must be integer 2"
