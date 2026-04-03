"""
Test for 'add-malli-schemas' skill — Metabase Malli Field API Schemas
Validates that the Agent added Malli schemas for the field API including
PositiveInt validation and schema definitions.
"""

import os
import re

import pytest


class TestAddMalliSchemas:
    """Verify Metabase Malli schema additions."""

    REPO_DIR = "/workspace/metabase"

    def test_malli_schema_file_exists(self):
        """Malli schema definitions for field API must exist."""
        found = False
        for root, dirs, files in os.walk(os.path.join(self.REPO_DIR, "src")):
            for f in files:
                if f.endswith(".clj") or f.endswith(".cljc"):
                    path = os.path.join(root, f)
                    with open(path, "r", errors="ignore") as fh:
                        content = fh.read()
                    if re.search(r"malli|:schema|ms/", content) and "field" in f.lower():
                        found = True
                        break
            if found:
                break
        assert found, "No Malli schema file found for field API"

    def test_positive_int_schema_defined(self):
        """ms/PositiveInt or equivalent positive integer schema must be defined."""
        found = False
        for root, dirs, files in os.walk(os.path.join(self.REPO_DIR, "src")):
            for f in files:
                if f.endswith(".clj") or f.endswith(".cljc"):
                    path = os.path.join(root, f)
                    with open(path, "r", errors="ignore") as fh:
                        content = fh.read()
                    if re.search(r"PositiveInt|pos-int|positive-int", content):
                        found = True
                        break
            if found:
                break
        assert found, "PositiveInt schema not defined"

    def test_field_api_uses_malli_validation(self):
        """Field API endpoint must use Malli schema validation."""
        found = False
        for root, dirs, files in os.walk(os.path.join(self.REPO_DIR, "src")):
            for f in files:
                if f.endswith(".clj") and "field" in f.lower():
                    path = os.path.join(root, f)
                    with open(path, "r", errors="ignore") as fh:
                        content = fh.read()
                    if re.search(r"mu/defendpoint|defendpoint|:malli|schema", content):
                        found = True
                        break
            if found:
                break
        assert found, "Field API does not use Malli validation"

    def test_schema_has_field_id_validation(self):
        """Schema must validate field-id parameter."""
        found = False
        for root, dirs, files in os.walk(os.path.join(self.REPO_DIR, "src")):
            for f in files:
                if f.endswith(".clj") and "field" in f.lower():
                    path = os.path.join(root, f)
                    with open(path, "r", errors="ignore") as fh:
                        content = fh.read()
                    if re.search(r"field.id|field-id|:id\s+ms/PositiveInt", content):
                        found = True
                        break
            if found:
                break
        assert found, "Schema does not validate field-id"

    def test_schema_uses_malli_registry(self):
        """Schema should use Malli registry (mr/def or mc/defschema)."""
        found = False
        for root, dirs, files in os.walk(os.path.join(self.REPO_DIR, "src")):
            for f in files:
                if f.endswith(".clj") or f.endswith(".cljc"):
                    path = os.path.join(root, f)
                    with open(path, "r", errors="ignore") as fh:
                        content = fh.read()
                    if re.search(r"mr/def|mc/defschema|mu/defschema|def.*schema", content) and "field" in content.lower():
                        found = True
                        break
            if found:
                break
        assert found, "Schema does not use Malli registry functions"

    def test_endpoint_returns_field_data(self):
        """Field API endpoint must return field data."""
        found = False
        for root, dirs, files in os.walk(os.path.join(self.REPO_DIR, "src")):
            for f in files:
                if f.endswith(".clj") and "field" in f.lower():
                    path = os.path.join(root, f)
                    with open(path, "r", errors="ignore") as fh:
                        content = fh.read()
                    if re.search(r"api.*field|GET|PUT|POST", content) and re.search(r":body|respond|json", content):
                        found = True
                        break
            if found:
                break
        assert found, "Field API endpoint does not return field data"

    def test_schema_validates_request_body(self):
        """PUT/POST endpoints should validate request body via Malli schema."""
        found = False
        for root, dirs, files in os.walk(os.path.join(self.REPO_DIR, "src")):
            for f in files:
                if f.endswith(".clj") and "field" in f.lower():
                    path = os.path.join(root, f)
                    with open(path, "r", errors="ignore") as fh:
                        content = fh.read()
                    if re.search(r"PUT|POST", content) and re.search(r":body|:schema|malli", content):
                        found = True
                        break
            if found:
                break
        assert found, "PUT/POST endpoints missing Malli body validation"

    def test_test_file_exists_for_schemas(self):
        """Tests for the Malli schemas should exist."""
        found = False
        for root, dirs, files in os.walk(os.path.join(self.REPO_DIR, "test")):
            for f in files:
                if "field" in f.lower() and f.endswith((".clj", "_test.clj")):
                    found = True
                    break
            if found:
                break
        assert found, "No test file for field API schemas found"

    def test_schema_handles_optional_fields(self):
        """Schema should define optional fields with :optional or ?."""
        found = False
        for root, dirs, files in os.walk(os.path.join(self.REPO_DIR, "src")):
            for f in files:
                if f.endswith(".clj") and "field" in f.lower():
                    path = os.path.join(root, f)
                    with open(path, "r", errors="ignore") as fh:
                        content = fh.read()
                    if re.search(r":optional|optional\?|\?|maybe", content):
                        found = True
                        break
            if found:
                break
        assert found, "Schema does not handle optional fields"

    def test_no_raw_sql_in_field_api(self):
        """Field API should use Toucan/HoneySQL, not raw SQL strings."""
        found_raw_sql = False
        for root, dirs, files in os.walk(os.path.join(self.REPO_DIR, "src")):
            for f in files:
                if f.endswith(".clj") and "field" in f.lower():
                    path = os.path.join(root, f)
                    with open(path, "r", errors="ignore") as fh:
                        content = fh.read()
                    if re.search(r'jdbc/query.*"SELECT|"INSERT INTO|"UPDATE.*SET', content):
                        found_raw_sql = True
                        break
            if found_raw_sql:
                break
        assert not found_raw_sql, "Field API uses raw SQL instead of Toucan/HoneySQL"

    def test_malli_import_present(self):
        """Field API namespace must import malli or metabase.util.malli."""
        found = False
        for root, dirs, files in os.walk(os.path.join(self.REPO_DIR, "src")):
            for f in files:
                if f.endswith(".clj") and "field" in f.lower():
                    path = os.path.join(root, f)
                    with open(path, "r", errors="ignore") as fh:
                        content = fh.read()
                    if re.search(r"metabase\.util\.malli|malli\.core|mu/|ms/", content):
                        found = True
                        break
            if found:
                break
        assert found, "Field API does not import malli utilities"
