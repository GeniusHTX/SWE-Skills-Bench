"""
Test for 'add-admin-api-endpoint' skill — Ghost Announcements CRUD API
Validates that the Agent added an announcements CRUD API endpoint to Ghost,
including Bookshelf model, schema validation, and admin controller.
"""

import os
import re

import pytest


class TestAddAdminApiEndpoint:
    """Verify Ghost announcements admin API endpoint."""

    REPO_DIR = "/workspace/Ghost"

    def test_announcement_model_file_exists(self):
        """Announcement Bookshelf model must exist."""
        candidates = [
            os.path.join(self.REPO_DIR, "ghost", "core", "server", "models", "announcement.js"),
            os.path.join(self.REPO_DIR, "ghost", "core", "server", "models", "Announcement.js"),
        ]
        found = any(os.path.isfile(p) for p in candidates)
        if not found:
            models_dir = os.path.join(self.REPO_DIR, "ghost", "core", "server", "models")
            if os.path.isdir(models_dir):
                for f in os.listdir(models_dir):
                    if "announcement" in f.lower():
                        found = True
                        break
        assert found, "Announcement model file not found"

    def test_announcement_controller_file_exists(self):
        """Announcements admin controller must exist."""
        api_dir = os.path.join(self.REPO_DIR, "ghost", "core", "server", "api")
        found = False
        for root, dirs, files in os.walk(api_dir):
            for f in files:
                if "announcement" in f.lower():
                    found = True
                    break
            if found:
                break
        assert found, "Announcements controller file not found in api directory"

    def test_schema_validation_file_exists(self):
        """Input validation schema for announcements must exist."""
        schema_dir = os.path.join(self.REPO_DIR, "ghost", "core", "server", "api", "endpoints", "utils", "validators", "input")
        found = False
        if os.path.isdir(schema_dir):
            for f in os.listdir(schema_dir):
                if "announcement" in f.lower():
                    found = True
                    break
        if not found:
            for root, dirs, files in os.walk(os.path.join(self.REPO_DIR, "ghost")):
                for f in files:
                    if "announcement" in f.lower() and ("schema" in f.lower() or "valid" in f.lower()):
                        found = True
                        break
                if found:
                    break
        assert found, "Announcement schema/validation file not found"

    def test_model_extends_bookshelf(self):
        """Announcement model must extend Bookshelf Model or ghostBookshelf."""
        model_path = self._find_file("models", "announcement")
        if model_path is None:
            pytest.skip("Announcement model file not found")
        with open(model_path, "r", errors="ignore") as fh:
            content = fh.read()
        assert re.search(r"ghostBookshelf\.Model\.extend|Bookshelf|baseModel", content), (
            "Announcement model does not extend Bookshelf"
        )

    def test_model_defines_tablename(self):
        """Announcement model must define tableName."""
        model_path = self._find_file("models", "announcement")
        if model_path is None:
            pytest.skip("Announcement model file not found")
        with open(model_path, "r", errors="ignore") as fh:
            content = fh.read()
        assert re.search(r"tableName|table_name", content), (
            "Announcement model does not define tableName"
        )

    def test_controller_has_crud_methods(self):
        """Announcements controller must have browse, read, add, edit, destroy methods."""
        ctrl_path = self._find_file("api", "announcement")
        if ctrl_path is None:
            pytest.skip("Announcements controller not found")
        with open(ctrl_path, "r", errors="ignore") as fh:
            content = fh.read()
        methods = ["browse", "read", "add", "edit", "destroy"]
        found = sum(1 for m in methods if re.search(rf"\b{m}\b", content))
        assert found >= 3, (
            f"Controller only has {found}/5 CRUD methods"
        )

    def test_route_registered_for_announcements(self):
        """Route for /announcements/ must be registered."""
        found = False
        for root, dirs, files in os.walk(os.path.join(self.REPO_DIR, "ghost", "core", "server")):
            for f in files:
                if f.endswith(".js"):
                    path = os.path.join(root, f)
                    with open(path, "r", errors="ignore") as fh:
                        content = fh.read()
                    if re.search(r"announcements", content) and re.search(r"router|route|app\.(get|post|put|delete)", content):
                        found = True
                        break
            if found:
                break
        assert found, "No route registered for announcements"

    def test_schema_defines_required_fields(self):
        """Schema must define required fields for announcement creation."""
        schema_path = self._find_schema_file()
        if schema_path is None:
            pytest.skip("Schema file not found")
        with open(schema_path, "r", errors="ignore") as fh:
            content = fh.read()
        assert re.search(r"required|properties|title|content", content, re.IGNORECASE), (
            "Schema does not define required properties"
        )

    def test_controller_checks_permissions(self):
        """Controller must check admin permissions."""
        ctrl_path = self._find_file("api", "announcement")
        if ctrl_path is None:
            pytest.skip("Announcements controller not found")
        with open(ctrl_path, "r", errors="ignore") as fh:
            content = fh.read()
        assert re.search(r"permission|auth|staff|admin", content, re.IGNORECASE), (
            "Controller has no permission/auth checks"
        )

    def test_integration_test_exists(self):
        """Integration tests for announcements API must exist."""
        test_dir = os.path.join(self.REPO_DIR, "ghost", "core", "test")
        found = False
        for root, dirs, files in os.walk(test_dir if os.path.isdir(test_dir) else self.REPO_DIR):
            for f in files:
                if "announcement" in f.lower() and "test" in f.lower():
                    found = True
                    break
            if found:
                break
        assert found, "No integration test files for announcements"

    def test_migration_file_exists(self):
        """Database migration for announcements table must exist."""
        found = False
        migrations_dir = os.path.join(self.REPO_DIR, "ghost", "core", "server", "data", "migrations")
        if os.path.isdir(migrations_dir):
            for root, dirs, files in os.walk(migrations_dir):
                for f in files:
                    if "announcement" in f.lower():
                        found = True
                        break
                if found:
                    break
        if not found:
            for root, dirs, files in os.walk(os.path.join(self.REPO_DIR, "ghost")):
                for f in files:
                    if "announcement" in f.lower() and "migrat" in f.lower():
                        found = True
                        break
                if found:
                    break
        assert found, "No migration for announcements table found"

    def test_model_has_timestamps(self):
        """Model must include created_at/updated_at timestamp fields."""
        model_path = self._find_file("models", "announcement")
        if model_path is None:
            pytest.skip("Announcement model file not found")
        with open(model_path, "r", errors="ignore") as fh:
            content = fh.read()
        assert re.search(r"created_at|updated_at|hasTimestamps|timestamps", content), (
            "Announcement model has no timestamp fields"
        )

    def _find_file(self, subdir, keyword):
        base = os.path.join(self.REPO_DIR, "ghost", "core", "server", subdir)
        if not os.path.isdir(base):
            return None
        for root, dirs, files in os.walk(base):
            for f in files:
                if keyword in f.lower():
                    return os.path.join(root, f)
        return None

    def _find_schema_file(self):
        for root, dirs, files in os.walk(os.path.join(self.REPO_DIR, "ghost")):
            for f in files:
                if "announcement" in f.lower() and ("schema" in f.lower() or "valid" in f.lower()):
                    return os.path.join(root, f)
        return None
