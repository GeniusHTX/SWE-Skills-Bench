"""
Test for 'add-admin-api-endpoint' skill — Ghost Audit Logs Endpoint
Validates that the Agent created an audit_logs endpoint for the Ghost Admin API
with proper endpoint controller, service layer, and route registration.
"""

import os
import re
import subprocess

import pytest


class TestAddAdminApiEndpoint:
    """Verify Ghost Admin API audit_logs endpoint."""

    REPO_DIR = "/workspace/Ghost"

    def _read(self, *parts):
        fpath = os.path.join(self.REPO_DIR, *parts)
        assert os.path.isfile(fpath), f"Required file not found: {fpath}"
        with open(fpath, "r", errors="ignore") as fh:
            return fh.read()

    # ------------------------------------------------------------------
    # L1: File existence
    # ------------------------------------------------------------------

    def test_endpoint_controller_exists(self):
        """audit-logs.js endpoint controller must exist."""
        assert os.path.isfile(
            os.path.join(
                self.REPO_DIR, "ghost/core/core/server/api/endpoints/audit-logs.js"
            )
        )

    def test_service_layer_exists(self):
        """audit-log service index.js must exist."""
        assert os.path.isfile(
            os.path.join(
                self.REPO_DIR, "ghost/core/core/server/services/audit-log/index.js"
            )
        )

    # ------------------------------------------------------------------
    # L1: Syntax check
    # ------------------------------------------------------------------

    def test_endpoint_valid_js(self):
        """audit-logs.js must have valid JavaScript syntax."""
        result = subprocess.run(
            ["node", "--check", "ghost/core/core/server/api/endpoints/audit-logs.js"],
            cwd=self.REPO_DIR,
            capture_output=True,
            text=True,
            timeout=30,
        )
        assert result.returncode == 0, f"Syntax error:\n{result.stderr}"

    def test_service_valid_js(self):
        """audit-log service must have valid JavaScript syntax."""
        result = subprocess.run(
            ["node", "--check", "ghost/core/core/server/services/audit-log/index.js"],
            cwd=self.REPO_DIR,
            capture_output=True,
            text=True,
            timeout=30,
        )
        assert result.returncode == 0, f"Syntax error:\n{result.stderr}"

    # ------------------------------------------------------------------
    # L2: Endpoint structure
    # ------------------------------------------------------------------

    def test_endpoint_exports_browse(self):
        """Endpoint must export a browse handler."""
        content = self._read("ghost/core/core/server/api/endpoints/audit-logs.js")
        patterns = [r"browse", r"module\.exports", r"exports\.\w+"]
        found = sum(1 for p in patterns if re.search(p, content))
        assert found >= 2, "Endpoint does not appear to export browse handler"

    def test_endpoint_has_permission_check(self):
        """Endpoint must enforce admin permission."""
        content = self._read("ghost/core/core/server/api/endpoints/audit-logs.js")
        patterns = [
            r"permissions",
            r"admin",
            r"requireAdmin",
            r"canThis",
            r"permission",
        ]
        assert any(
            re.search(p, content, re.IGNORECASE) for p in patterns
        ), "Endpoint does not enforce permissions"

    def test_endpoint_supports_pagination(self):
        """Endpoint must support pagination."""
        content = self._read("ghost/core/core/server/api/endpoints/audit-logs.js")
        patterns = [
            r"page",
            r"limit",
            r"pagination",
            r"options\.page",
            r"options\.limit",
        ]
        assert any(
            re.search(p, content, re.IGNORECASE) for p in patterns
        ), "Endpoint does not support pagination"

    def test_endpoint_supports_filtering(self):
        """Endpoint must support filtering by action, actor, date."""
        content = self._read("ghost/core/core/server/api/endpoints/audit-logs.js")
        patterns = [r"filter", r"action", r"actor", r"date", r"options\.filter"]
        found = sum(1 for p in patterns if re.search(p, content, re.IGNORECASE))
        assert found >= 2, "Endpoint does not support filtering by action/actor/date"

    # ------------------------------------------------------------------
    # L2: Service layer
    # ------------------------------------------------------------------

    def test_service_has_query_logic(self):
        """Service must implement query logic."""
        content = self._read("ghost/core/core/server/services/audit-log/index.js")
        patterns = [r"query", r"find", r"browse", r"fetchAll", r"where"]
        assert any(
            re.search(p, content, re.IGNORECASE) for p in patterns
        ), "Service has no query logic"

    def test_service_defines_data_model(self):
        """Service or endpoint must define audit log data fields."""
        combined = self._read(
            "ghost/core/core/server/api/endpoints/audit-logs.js"
        ) + self._read("ghost/core/core/server/services/audit-log/index.js")
        fields = ["action", "actor", "target", "timestamp", "resource"]
        found = sum(1 for f in fields if re.search(f, combined, re.IGNORECASE))
        assert found >= 3, f"Only {found}/5 expected data fields found"

    # ------------------------------------------------------------------
    # L2: Route registration
    # ------------------------------------------------------------------

    def test_route_registered_in_endpoints(self):
        """audit_logs route must be registered in endpoints.js."""
        endpoints_path = os.path.join(
            self.REPO_DIR, "ghost/core/core/server/web/api/endpoints.js"
        )
        assert os.path.isfile(endpoints_path), "endpoints.js not found"
        with open(endpoints_path, "r", errors="ignore") as fh:
            content = fh.read()
        patterns = [r"audit.log", r"audit_log", r"auditLog"]
        assert any(
            re.search(p, content, re.IGNORECASE) for p in patterns
        ), "audit_logs route not registered in endpoints.js"

    # ------------------------------------------------------------------
    # L2: Response format
    # ------------------------------------------------------------------

    def test_response_follows_ghost_envelope(self):
        """Response must follow Ghost's API envelope structure."""
        content = self._read("ghost/core/core/server/api/endpoints/audit-logs.js")
        patterns = [r"audit_logs", r"meta", r"pagination"]
        found = sum(1 for p in patterns if re.search(p, content, re.IGNORECASE))
        assert found >= 2, "Response does not follow Ghost API envelope structure"
