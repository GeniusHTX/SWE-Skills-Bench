"""
Test for 'clojure-write' skill — Metadata Audit Log for Metabase
Validates that the Agent created the MetadataAuditLog model, API endpoints,
event handler, and SQL migration in the Metabase Clojure codebase.
"""

import os
import re

import pytest


class TestClojureWrite:
    """Verify MetadataAuditLog Clojure implementation in Metabase."""

    REPO_DIR = "/workspace/metabase"

    # ---- helpers ----

    @staticmethod
    def _read(path):
        with open(path, "r", errors="ignore") as fh:
            return fh.read()

    def _model_f(self):
        return os.path.join(self.REPO_DIR, "src/metabase/models/metadata_audit_log.clj")

    def _api_f(self):
        return os.path.join(self.REPO_DIR, "src/metabase/api/metadata_audit.clj")

    def _event_f(self):
        return os.path.join(self.REPO_DIR, "src/metabase/events/metadata_audit.clj")

    def _migration_f(self):
        return os.path.join(
            self.REPO_DIR,
            "resources/migrations/001_create_metadata_audit_log.sql",
        )

    # ---- file_path_check ----

    def test_model_clj_exists(self):
        """Verifies src/metabase/models/metadata_audit_log.clj exists."""
        assert os.path.exists(
            self._model_f()
        ), f"Model file not found: {self._model_f()}"

    def test_api_clj_exists(self):
        """Verifies src/metabase/api/metadata_audit.clj exists."""
        assert os.path.exists(self._api_f()), f"API file not found: {self._api_f()}"

    def test_events_clj_exists(self):
        """Verifies src/metabase/events/metadata_audit.clj exists."""
        assert os.path.exists(
            self._event_f()
        ), f"Events file not found: {self._event_f()}"

    def test_migration_sql_exists(self):
        """Verifies resources/migrations/001_create_metadata_audit_log.sql exists."""
        assert os.path.exists(
            self._migration_f()
        ), f"Migration SQL not found: {self._migration_f()}"

    # ---- semantic_check ----

    def test_sem_model_entity_name(self):
        """Verifies MetadataAuditLog or metadata_audit_log in model."""
        model_text = self._read(self._model_f())
        assert (
            "MetadataAuditLog" in model_text or "metadata_audit_log" in model_text
        ), "Model entity name missing"

    def test_sem_json_type_old_value(self):
        """Verifies :json type for old_value in model."""
        model_text = self._read(self._model_f())
        assert ":json" in model_text and (
            "old_value" in model_text or "old-value" in model_text
        ), ":json type for old_value missing"

    def test_sem_api_text_readable(self):
        """Verifies api/metadata_audit.clj is readable."""
        api_text = self._read(self._api_f())
        assert len(api_text) > 0, "API file is empty"

    def test_sem_defendpoint_in_api(self):
        """Verifies defendpoint forms in metadata_audit.clj."""
        api_text = self._read(self._api_f())
        assert "defendpoint" in api_text, "No defendpoint forms in metadata_audit.clj"

    def test_sem_id_endpoint(self):
        """Verifies GET by ID endpoint (:id) in API."""
        api_text = self._read(self._api_f())
        assert ":id" in api_text or "id" in api_text, "GET by ID endpoint missing"

    # ---- functional_check ----

    def test_func_log_change_function(self):
        """Verifies log-change! function defined in model ns."""
        model_text = self._read(self._model_f())
        assert (
            "log-change!" in model_text or "defn log-change" in model_text
        ), "log-change! function not defined in model ns"

    def test_func_ex_info_validation(self):
        """Verifies ex-info validation in log-change!."""
        model_text = self._read(self._model_f())
        assert "ex-info" in model_text, "ex-info validation not found in log-change!"

    def test_func_migration_create_table(self):
        """Verifies migration SQL has CREATE TABLE."""
        migration_text = self._read(self._migration_f())
        assert (
            "CREATE TABLE" in migration_text.upper()
            and "metadata_audit_log" in migration_text
        ), "Migration SQL missing CREATE TABLE"

    def test_func_migration_columns(self):
        """Verifies all required columns in migration SQL."""
        migration_text = self._read(self._migration_f())
        required_cols = [
            "entity_type",
            "entity_id",
            "action",
            "old_value",
            "new_value",
            "user_id",
            "created_at",
        ]
        for col in required_cols:
            assert col in migration_text, f"Column {col} missing from migration SQL"

    def test_func_superuser_check(self):
        """Verifies admin permission check in API."""
        api_text = self._read(self._api_f())
        assert (
            "require-superuser" in api_text
            or "check-superuser" in api_text
            or "superuser" in api_text
        ), "Admin permission check missing in API"

    def test_func_event_handler(self):
        """Verifies event handler references log-change or audit."""
        events_text = self._read(self._event_f())
        assert (
            "log-change" in events_text
            or "audit" in events_text
            or "process-event" in events_text
        ), "Event handler does not reference log-change or audit"

    def test_func_status_code_400(self):
        """Failure case: Invalid entity_type -> ex-info :status-code 400."""
        model_text = self._read(self._model_f())
        assert (
            ":status-code" in model_text or "status-code" in model_text
        ), "No :status-code handling for invalid entity_type"
        assert (
            "400" in model_text or "ex-info" in model_text
        ), "No 400 error response for invalid input"

    def test_func_ns_declaration(self):
        """Verifies proper namespace declaration in model."""
        model_text = self._read(self._model_f())
        assert re.search(
            r"\(ns\s+metabase\.models\.metadata[_-]audit[_-]log", model_text
        ), "Namespace declaration missing or incorrect"
