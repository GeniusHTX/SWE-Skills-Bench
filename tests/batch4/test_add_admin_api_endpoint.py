"""
Test for 'add-admin-api-endpoint' skill — Ghost Admin Announcements API
Validates that the Agent created the announcements admin API endpoint
with controller, model, routes, and e2e tests for the Ghost blogging platform.
"""

import os

import pytest


class TestAddAdminApiEndpoint:
    """Verify Ghost admin announcements API endpoint implementation."""

    REPO_DIR = "/workspace/Ghost"

    # ---- helpers ----

    @staticmethod
    def _read(path):
        with open(path, "r", errors="ignore") as fh:
            return fh.read()

    def _find_file(self, filename, start_dir=None):
        """Walk the repo to find a file by name."""
        start = start_dir or self.REPO_DIR
        for root, _dirs, files in os.walk(start):
            if filename in files:
                return os.path.join(root, filename)
        return None

    # ---- file_path_check ----

    def test_server_directory_exists(self):
        """Verifies ghost/core/core/server directory exists."""
        path = os.path.join(self.REPO_DIR, "ghost/core/core/server")
        assert os.path.exists(path), f"Expected path not found: {path}"

    def test_announcements_endpoint_exists(self):
        """Verifies api/endpoints/announcements.js exists."""
        found = self._find_file("announcements.js")
        assert found is not None, "announcements.js not found in repo"

    def test_announcement_model_exists(self):
        """Verifies models/announcement.js exists."""
        found = self._find_file("announcement.js")
        assert found is not None, "announcement.js model not found in repo"

    def test_admin_routes_exists(self):
        """Verifies web/api/endpoints/admin/routes.js exists."""
        found = self._find_file("routes.js", os.path.join(self.REPO_DIR, "web"))
        if found is None:
            found = self._find_file(
                "routes.js",
                os.path.join(self.REPO_DIR, "ghost/core/core/server/web"),
            )
        assert found is not None, "admin routes.js not found"

    # ---- semantic_check ----

    def test_sem_controller_readable(self):
        """Reads the announcements controller file."""
        server_dir = os.path.join(self.REPO_DIR, "ghost/core/core/server")
        ctrl = None
        for root, _dirs, files in os.walk(server_dir):
            for f in files:
                if "announcements" in f.lower() and f.endswith(".js"):
                    p = os.path.join(root, f)
                    ctrl = self._read(p)
                    break
            if ctrl:
                break
        assert ctrl is not None and len(ctrl) > 0, "Controller file not readable"

    def test_sem_docname_announcements(self):
        """Verifies docName: 'announcements' in controller."""
        server_dir = os.path.join(self.REPO_DIR, "ghost/core/core/server")
        ctrl_text = ""
        for root, _dirs, files in os.walk(server_dir):
            for f in files:
                if "announcements" in f.lower() and f.endswith(".js"):
                    ctrl_text = self._read(os.path.join(root, f))
                    break
            if ctrl_text:
                break
        assert (
            "docName: 'announcements'" in ctrl_text or "docName:" in ctrl_text
        ), "docName missing in controller"

    def test_sem_crud_methods_present(self):
        """Verifies browse/read/add/edit/destroy methods in controller."""
        server_dir = os.path.join(self.REPO_DIR, "ghost/core/core/server")
        ctrl_text = ""
        for root, _dirs, files in os.walk(server_dir):
            for f in files:
                if "announcements" in f.lower() and f.endswith(".js"):
                    ctrl_text = self._read(os.path.join(root, f))
                    break
            if ctrl_text:
                break
        for method in ["browse", "read", "add", "edit", "destroy"]:
            assert method in ctrl_text, f"{method} missing in controller"

    def test_sem_permissions_on_all_methods(self):
        """Verifies permissions set on all methods (edge case)."""
        server_dir = os.path.join(self.REPO_DIR, "ghost/core/core/server")
        ctrl_text = ""
        for root, _dirs, files in os.walk(server_dir):
            for f in files:
                if "announcements" in f.lower() and f.endswith(".js"):
                    ctrl_text = self._read(os.path.join(root, f))
                    break
            if ctrl_text:
                break
        assert (
            ctrl_text.count("permissions: true") >= 5
            or ctrl_text.count("permissions:") >= 5
        ), "permissions not set on all methods"

    def test_sem_routes_readable(self):
        """Reads admin routes file."""
        routes = None
        for search_dir in [
            os.path.join(self.REPO_DIR, "web"),
            os.path.join(self.REPO_DIR, "ghost/core/core/server/web"),
        ]:
            if not os.path.isdir(search_dir):
                continue
            for root, _dirs, files in os.walk(search_dir):
                if "routes.js" in files:
                    routes = self._read(os.path.join(root, "routes.js"))
                    break
            if routes:
                break
        assert routes is not None and len(routes) > 0, "Routes file not readable"

    def test_sem_announcements_registered_in_routes(self):
        """Verifies 'announcements' registered in admin routes."""
        routes_text = ""
        for search_dir in [
            os.path.join(self.REPO_DIR, "web"),
            os.path.join(self.REPO_DIR, "ghost/core/core/server/web"),
        ]:
            if not os.path.isdir(search_dir):
                continue
            for root, _dirs, files in os.walk(search_dir):
                if "routes.js" in files:
                    routes_text = self._read(os.path.join(root, "routes.js"))
                    break
            if routes_text:
                break
        assert (
            "announcements" in routes_text
        ), "announcements not registered in admin routes"

    # ---- functional_check ----

    def test_func_title_max_length_validation(self):
        """Verifies title max length (255) validation in controller."""
        server_dir = os.path.join(self.REPO_DIR, "ghost/core/core/server")
        ctrl_text = ""
        for root, _dirs, files in os.walk(server_dir):
            for f in files:
                if "announcements" in f.lower() and f.endswith(".js"):
                    ctrl_text = self._read(os.path.join(root, f))
                    break
            if ctrl_text:
                break
        assert (
            "title" in ctrl_text and "255" in ctrl_text
        ), "title max length validation not found"

    def test_func_content_max_length_validation(self):
        """Verifies content max length (2000) validation in controller."""
        server_dir = os.path.join(self.REPO_DIR, "ghost/core/core/server")
        ctrl_text = ""
        for root, _dirs, files in os.walk(server_dir):
            for f in files:
                if "announcements" in f.lower() and f.endswith(".js"):
                    ctrl_text = self._read(os.path.join(root, f))
                    break
            if ctrl_text:
                break
        assert (
            "content" in ctrl_text and "2000" in ctrl_text
        ), "content max length validation not found"

    def test_func_visibility_field(self):
        """Verifies visibility field handling in controller."""
        server_dir = os.path.join(self.REPO_DIR, "ghost/core/core/server")
        ctrl_text = ""
        for root, _dirs, files in os.walk(server_dir):
            for f in files:
                if "announcements" in f.lower() and f.endswith(".js"):
                    ctrl_text = self._read(os.path.join(root, f))
                    break
            if ctrl_text:
                break
        assert "visibility" in ctrl_text, "visibility field handling missing"

    def test_func_visibility_enum_values(self):
        """Verifies visibility enum values (public) defined."""
        server_dir = os.path.join(self.REPO_DIR, "ghost/core/core/server")
        ctrl_text = ""
        for root, _dirs, files in os.walk(server_dir):
            for f in files:
                if "announcements" in f.lower() and f.endswith(".js"):
                    ctrl_text = self._read(os.path.join(root, f))
                    break
            if ctrl_text:
                break
        assert (
            "'public'" in ctrl_text or '"public"' in ctrl_text
        ), "visibility enum values not defined"

    def test_func_e2e_test_readable(self):
        """Reads e2e test file for announcements."""
        e2e = os.path.join(
            self.REPO_DIR,
            "ghost/core/test/e2e-api/admin/announcements.test.js",
        )
        e2e_text = self._read(e2e)
        assert len(e2e_text) > 0, "e2e test file is empty"

    def test_func_e2e_201_success_case(self):
        """Verifies e2e test covers 201 success case."""
        e2e = os.path.join(
            self.REPO_DIR,
            "ghost/core/test/e2e-api/admin/announcements.test.js",
        )
        e2e_text = self._read(e2e)
        assert (
            "201" in e2e_text or "Created" in e2e_text
        ), "e2e test missing 201 success case"

    def test_func_e2e_422_validation_case(self):
        """Verifies e2e test covers 422 validation error case."""
        e2e = os.path.join(
            self.REPO_DIR,
            "ghost/core/test/e2e-api/admin/announcements.test.js",
        )
        e2e_text = self._read(e2e)
        assert (
            "422" in e2e_text or "Unprocessable" in e2e_text
        ), "e2e test missing 422 validation case"

    def test_func_e2e_403_auth_case(self):
        """Verifies e2e test covers 403 authorization case."""
        e2e = os.path.join(
            self.REPO_DIR,
            "ghost/core/test/e2e-api/admin/announcements.test.js",
        )
        e2e_text = self._read(e2e)
        assert (
            "403" in e2e_text
            or "Forbidden" in e2e_text
            or "unauthori" in e2e_text.lower()
        ), "e2e test missing 403 auth case"

    def test_func_failure_post_missing_title_422(self):
        """Failure case: POST missing title should produce 422."""
        e2e = os.path.join(
            self.REPO_DIR,
            "ghost/core/test/e2e-api/admin/announcements.test.js",
        )
        e2e_text = self._read(e2e)
        assert (
            "422" in e2e_text or "Unprocessable" in e2e_text
        ), "No 422 failure test case found for missing title"
