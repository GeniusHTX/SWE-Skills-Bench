"""
Test for 'dbt-transformation-patterns' skill — dbt-core ecommerce pipeline
Validates that the Agent created a dbt project with staging models, mart models,
YAML schema configs, and testing patterns.
"""

import os
import re

import pytest


class TestDbtTransformationPatterns:
    """Verify dbt ecommerce transformation pipeline."""

    REPO_DIR = "/workspace/dbt-core"

    def test_dbt_project_yml_exists(self):
        """dbt_project.yml must exist."""
        found = False
        for root, dirs, files in os.walk(self.REPO_DIR):
            if "dbt_project.yml" in files:
                found = True
                break
        assert found, "dbt_project.yml not found"

    def test_staging_models_directory_exists(self):
        """Staging models directory must exist."""
        found = False
        for root, dirs, files in os.walk(self.REPO_DIR):
            for d in dirs:
                if d == "staging":
                    found = True
                    break
            if found:
                break
        assert found, "staging directory not found"

    def test_mart_models_directory_exists(self):
        """Mart models directory must exist (marts or mart)."""
        found = False
        for root, dirs, files in os.walk(self.REPO_DIR):
            for d in dirs:
                if d in ("marts", "mart"):
                    found = True
                    break
            if found:
                break
        assert found, "marts directory not found"

    def test_staging_sql_model_exists(self):
        """At least one staging SQL model must be present."""
        found = False
        for root, dirs, files in os.walk(self.REPO_DIR):
            if "staging" in root:
                for f in files:
                    if f.endswith(".sql") and f.startswith("stg_"):
                        found = True
                        break
            if found:
                break
        assert found, "No staging SQL model (stg_*.sql) found"

    def test_mart_sql_model_exists(self):
        """At least one mart SQL model must be present."""
        found = False
        for root, dirs, files in os.walk(self.REPO_DIR):
            if "mart" in root:
                for f in files:
                    if f.endswith(".sql"):
                        found = True
                        break
            if found:
                break
        assert found, "No mart SQL model found"

    def test_schema_yml_exists(self):
        """Schema YAML config must exist for model documentation/testing."""
        found = False
        for root, dirs, files in os.walk(self.REPO_DIR):
            for f in files:
                if f in ("schema.yml", "schema.yaml", "_schema.yml"):
                    found = True
                    break
                if f.endswith((".yml", ".yaml")) and "schema" in f.lower():
                    found = True
                    break
            if found:
                break
        assert found, "No schema YAML found"

    def test_staging_model_uses_source(self):
        """Staging model should reference a source()."""
        found = False
        for root, dirs, files in os.walk(self.REPO_DIR):
            if "staging" in root:
                for f in files:
                    if f.endswith(".sql"):
                        path = os.path.join(root, f)
                        with open(path, "r", errors="ignore") as fh:
                            content = fh.read()
                        if re.search(r"\{\{\s*source\s*\(", content):
                            found = True
                            break
            if found:
                break
        assert found, "No staging model uses source()"

    def test_mart_model_uses_ref(self):
        """Mart model should reference staging via ref()."""
        found = False
        for root, dirs, files in os.walk(self.REPO_DIR):
            if "mart" in root:
                for f in files:
                    if f.endswith(".sql"):
                        path = os.path.join(root, f)
                        with open(path, "r", errors="ignore") as fh:
                            content = fh.read()
                        if re.search(r"\{\{\s*ref\s*\(", content):
                            found = True
                            break
            if found:
                break
        assert found, "No mart model uses ref()"

    def test_schema_defines_tests(self):
        """Schema YAML must define column-level tests."""
        found = False
        for root, dirs, files in os.walk(self.REPO_DIR):
            for f in files:
                if f.endswith((".yml", ".yaml")):
                    path = os.path.join(root, f)
                    with open(path, "r", errors="ignore") as fh:
                        content = fh.read()
                    if re.search(r"tests:|not_null|unique|accepted_values|relationships", content):
                        found = True
                        break
            if found:
                break
        assert found, "Schema YAML does not define tests"

    def test_sources_yml_exists(self):
        """A sources.yml or sources definition must exist."""
        found = False
        for root, dirs, files in os.walk(self.REPO_DIR):
            for f in files:
                if f.endswith((".yml", ".yaml")):
                    path = os.path.join(root, f)
                    with open(path, "r", errors="ignore") as fh:
                        content = fh.read()
                    if re.search(r"sources:", content):
                        found = True
                        break
            if found:
                break
        assert found, "No sources definition found"

    def test_model_materialization_configured(self):
        """At least one model should have materialization configured (table/view/incremental)."""
        found = False
        for root, dirs, files in os.walk(self.REPO_DIR):
            for f in files:
                if f.endswith(".sql") or f.endswith((".yml", ".yaml")):
                    path = os.path.join(root, f)
                    with open(path, "r", errors="ignore") as fh:
                        content = fh.read()
                    if re.search(r"materialized\s*[=:]\s*['\"]?(table|view|incremental|ephemeral)", content):
                        found = True
                        break
            if found:
                break
        assert found, "No model materialization configured"
