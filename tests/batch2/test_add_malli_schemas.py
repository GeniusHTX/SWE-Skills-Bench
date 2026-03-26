"""
Test for 'add-malli-schemas' skill — Malli Schema Validation for Alert API
Validates that the Agent added Malli schema definitions and validation
integration to Metabase's alert API endpoints.
"""

import os
import re

import pytest


class TestAddMalliSchemas:
    """Verify Malli schema validation for Metabase alert API."""

    REPO_DIR = "/workspace/metabase"

    def _read(self, *parts):
        fpath = os.path.join(self.REPO_DIR, *parts)
        assert os.path.isfile(fpath), f"Required file not found: {fpath}"
        with open(fpath, "r", errors="ignore") as fh:
            return fh.read()

    # ------------------------------------------------------------------
    # L1: File existence
    # ------------------------------------------------------------------

    def test_schema_file_exists(self):
        """src/metabase/api/schema/alert.clj must exist."""
        assert os.path.isfile(
            os.path.join(self.REPO_DIR, "src/metabase/api/schema/alert.clj")
        )

    def test_alert_api_file_exists(self):
        """src/metabase/api/alert.clj must exist."""
        assert os.path.isfile(os.path.join(self.REPO_DIR, "src/metabase/api/alert.clj"))

    # ------------------------------------------------------------------
    # L1: Clojure namespace structure
    # ------------------------------------------------------------------

    def test_schema_has_namespace(self):
        """Schema file must declare a Clojure namespace."""
        content = self._read("src/metabase/api/schema/alert.clj")
        assert re.search(r"\(ns\s+", content), "Schema file has no (ns ...) declaration"

    def test_schema_uses_malli(self):
        """Schema file must import/use Malli."""
        content = self._read("src/metabase/api/schema/alert.clj")
        patterns = [r"malli", r":malli", r"mu/", r"mc/", r"m/", r"malli\.core"]
        assert any(
            re.search(p, content) for p in patterns
        ), "Schema file does not use Malli"

    # ------------------------------------------------------------------
    # L2: Schema definitions
    # ------------------------------------------------------------------

    def test_schema_defines_alert_creation(self):
        """Schema must define an alert creation schema."""
        content = self._read("src/metabase/api/schema/alert.clj")
        patterns = [
            r"create",
            r"Create",
            r"new-alert",
            r"AlertCreate",
            r"create-schema",
        ]
        assert any(
            re.search(p, content, re.IGNORECASE) for p in patterns
        ), "No alert creation schema found"

    def test_schema_has_required_fields(self):
        """Schema must specify required fields for alerts."""
        content = self._read("src/metabase/api/schema/alert.clj")
        # Look for field names common to an alert definition
        fields = ["name", "condition", "channel", "schedule", "card", "alert"]
        found = sum(1 for f in fields if re.search(rf":{f}", content, re.IGNORECASE))
        assert found >= 2, f"Only {found} expected alert fields found in schema"

    def test_schema_uses_malli_types(self):
        """Schema must use proper Malli type specifications."""
        content = self._read("src/metabase/api/schema/alert.clj")
        malli_types = [
            r":string",
            r":int",
            r":boolean",
            r":map",
            r":enum",
            r":sequential",
            r":keyword",
            r"pos-int",
            r"string\?",
        ]
        found = sum(1 for t in malli_types if re.search(t, content))
        assert found >= 2, f"Only {found} Malli type(s) found — need at least 2"

    def test_schema_marks_optional_fields(self):
        """Schema should distinguish required from optional fields."""
        content = self._read("src/metabase/api/schema/alert.clj")
        patterns = [r":optional", r"optional", r"\?", r"maybe"]
        assert any(
            re.search(p, content) for p in patterns
        ), "Schema does not distinguish optional fields"

    # ------------------------------------------------------------------
    # L2: API integration
    # ------------------------------------------------------------------

    def test_alert_api_imports_schema(self):
        """alert.clj must import the schema namespace."""
        content = self._read("src/metabase/api/alert.clj")
        patterns = [r"schema\.alert", r"schema/alert", r"api\.schema\.alert"]
        assert any(
            re.search(p, content) for p in patterns
        ), "alert.clj does not import schema namespace"

    def test_alert_api_validates_input(self):
        """alert.clj must validate incoming request data."""
        content = self._read("src/metabase/api/alert.clj")
        patterns = [
            r"validate",
            r"coerce",
            r"decode",
            r"explain",
            r"check",
            r"malli",
            r"schema",
        ]
        assert any(
            re.search(p, content, re.IGNORECASE) for p in patterns
        ), "alert.clj does not validate requests"

    def test_error_response_on_invalid_payload(self):
        """Invalid payloads should return 400 with error details."""
        content = self._read("src/metabase/api/alert.clj")
        patterns = [
            r"400",
            r"bad-request",
            r"validation.*error",
            r"error.*response",
            r"invalid",
        ]
        assert any(
            re.search(p, content, re.IGNORECASE) for p in patterns
        ), "No 400 error response logic for invalid payloads"

    def test_schema_covers_modification(self):
        """Schema should cover both creation and modification operations."""
        content = self._read("src/metabase/api/schema/alert.clj")
        patterns = [r"update", r"modify", r"Update", r"Modify", r"put", r"PUT"]
        assert any(
            re.search(p, content, re.IGNORECASE) for p in patterns
        ), "Schema does not cover modification operations"
