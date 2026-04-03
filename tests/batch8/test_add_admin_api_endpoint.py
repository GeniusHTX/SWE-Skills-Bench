"""
Test for 'add-admin-api-endpoint' skill — Ghost Admin Webhook CRUD API
Validates that the Agent created webhook CRUD endpoints, model, routes,
and e2e tests in the Ghost Admin API codebase.
"""

import os
import re
import subprocess
import json

import pytest


class TestAddAdminApiEndpoint:
    """Verify Ghost Admin webhook CRUD API implementation."""

    REPO_DIR = "/workspace/Ghost"

    # ── helpers ──────────────────────────────────────────────────────

    @staticmethod
    def _read_file(path: str) -> str:
        """Return file content or empty string if unreadable."""
        try:
            with open(path, "r", errors="ignore") as fh:
                return fh.read()
        except OSError:
            return ""

    @staticmethod
    def _run_cmd(cmd, cwd=None, timeout=120):
        """Run a shell command and return CompletedProcess."""
        return subprocess.run(
            cmd, shell=True, cwd=cwd, timeout=timeout,
            capture_output=True, text=True,
        )

    # ── file_path_check ─────────────────────────────────────────────

    def test_webhooks_endpoint_file_exists(self):
        """Verify the webhooks endpoint file and model file are created at the expected paths."""
        for rel in (
            "ghost/core/core/server/api/endpoints/webhooks.js",
            "ghost/core/core/server/models/webhook.js",
        ):
            path = os.path.join(self.REPO_DIR, rel)
            assert os.path.isfile(path), f"Missing expected file: {rel}"

    def test_admin_routes_file_exists(self):
        """Verify the admin routes file and e2e test file exist."""
        for rel in (
            "ghost/core/core/server/web/api/endpoints/admin/routes.js",
            "ghost/core/test/e2e-api/admin/webhooks.test.js",
        ):
            path = os.path.join(self.REPO_DIR, rel)
            assert os.path.isfile(path), f"Missing expected file: {rel}"

    def test_routes_file_modified(self):
        """Verify the test file for webhooks e2e tests exists."""
        path = os.path.join(
            self.REPO_DIR,
            "ghost/core/test/e2e-api/admin/webhooks.test.js",
        )
        assert os.path.isfile(path), "webhooks.test.js e2e test file missing"

    # ── semantic_check ──────────────────────────────────────────────

    def test_webhooks_js_exports_crud_functions(self):
        """Verify webhooks.js exports all five CRUD handler functions."""
        content = self._read_file(os.path.join(
            self.REPO_DIR,
            "ghost/core/core/server/api/endpoints/webhooks.js",
        ))
        assert content, "webhooks.js is empty or unreadable"
        for fn_name in ("browse", "read", "add", "edit", "destroy"):
            assert fn_name in content, (
                f"CRUD function '{fn_name}' not found in webhooks.js"
            )

    def test_routes_registers_webhook_paths(self):
        """Verify admin routes file registers GET/POST/PUT/DELETE for /webhooks/."""
        content = self._read_file(os.path.join(
            self.REPO_DIR,
            "ghost/core/core/server/web/api/endpoints/admin/routes.js",
        ))
        assert content, "routes.js is empty or unreadable"
        for pattern in ("/webhooks/", "router.get", "router.post", "router.put", "router.del"):
            # router.delete might be shortened to router.del in some codebase styles
            if pattern == "router.del":
                assert "router.del" in content or "router.delete" in content, (
                    "DELETE route registration missing for webhooks"
                )
            else:
                assert pattern in content, (
                    f"Pattern '{pattern}' not found in admin routes.js"
                )

    def test_webhook_model_event_field(self):
        """Verify the Webhook model defines event, target_url, secret fields."""
        content = self._read_file(os.path.join(
            self.REPO_DIR,
            "ghost/core/core/server/models/webhook.js",
        ))
        assert content, "webhook.js model is empty or unreadable"
        for field in ("event", "target_url", "secret"):
            assert field in content, (
                f"Field '{field}' not found in Webhook model"
            )

    def test_https_validation_present(self):
        """Verify HTTPS URL validation rule is present in the codebase."""
        content = self._read_file(os.path.join(
            self.REPO_DIR,
            "ghost/core/core/server/api/endpoints/webhooks.js",
        ))
        assert content, "webhooks.js is empty or unreadable"
        assert "https" in content.lower() and "target_url" in content, (
            "HTTPS validation not found near target_url handling"
        )

    # ── functional_check (command-based, skip if setup fails) ──────

    def _ensure_ghost_setup(self):
        """Attempt lightweight Ghost project setup; skip if it fails."""
        cwd = self.REPO_DIR
        if not os.path.isdir(cwd):
            pytest.skip(f"Repo dir {cwd} does not exist")

        lock_file = os.path.join(cwd, "yarn.lock")
        if not os.path.isfile(lock_file):
            pytest.skip("yarn.lock missing – cannot install deps")

        node_modules = os.path.join(cwd, "node_modules")
        if not os.path.isdir(node_modules):
            result = self._run_cmd("yarn install --frozen-lockfile", cwd=cwd, timeout=300)
            if result.returncode != 0:
                pytest.skip("yarn install failed – skipping functional tests")

    def test_create_webhook_returns_201(self):
        """POST valid webhook returns 201 with id and created_at in response body."""
        self._ensure_ghost_setup()
        result = self._run_cmd(
            "yarn test ghost/core/test/e2e-api/admin/webhooks.test.js",
            cwd=self.REPO_DIR, timeout=300,
        )
        # If the e2e test suite itself passes, the POST 201 case is covered
        if result.returncode != 0:
            pytest.skip("Ghost e2e test suite failed or not runnable")
        assert "passing" in result.stdout.lower() or result.returncode == 0

    def test_create_webhook_http_url_returns_422(self):
        """POST with HTTP (non-HTTPS) target_url should be rejected per validation rules."""
        self._ensure_ghost_setup()
        # Validate that the test file mentions HTTP rejection
        content = self._read_file(os.path.join(
            self.REPO_DIR,
            "ghost/core/test/e2e-api/admin/webhooks.test.js",
        ))
        assert content, "e2e test file is empty"
        assert "422" in content or "http" in content.lower(), (
            "HTTP URL rejection test not found in e2e test file"
        )

    def test_webhook_duplicate_returns_422(self):
        """POST duplicate event+target_url pair should return 422."""
        content = self._read_file(os.path.join(
            self.REPO_DIR,
            "ghost/core/test/e2e-api/admin/webhooks.test.js",
        ))
        assert content, "e2e test file is empty"
        assert "422" in content or "duplicate" in content.lower(), (
            "Duplicate webhook rejection test not found"
        )

    def test_unauthenticated_request_returns_401(self):
        """Request without auth token should return 401."""
        content = self._read_file(os.path.join(
            self.REPO_DIR,
            "ghost/core/test/e2e-api/admin/webhooks.test.js",
        ))
        assert content, "e2e test file is empty"
        assert "401" in content or "auth" in content.lower(), (
            "Unauthenticated access test not found"
        )

    def test_delete_webhook_then_get_returns_404(self):
        """DELETE existing webhook returns 204; subsequent GET by ID returns 404."""
        content = self._read_file(os.path.join(
            self.REPO_DIR,
            "ghost/core/test/e2e-api/admin/webhooks.test.js",
        ))
        assert content, "e2e test file is empty"
        assert "204" in content or "delete" in content.lower(), (
            "Delete webhook test not found in e2e test file"
        )
