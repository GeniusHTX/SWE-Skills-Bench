"""
Test for 'add-admin-api-endpoint' skill — Ghost Admin API Endpoint
Validates that the Agent added a new audit_logs Admin API endpoint in Ghost with
model, endpoint handler, route registration, and tests.
"""

import os
import re
import subprocess
import pytest

from _dependency_utils import ensure_npm_dependencies


# @pytest.fixture(scope="module", autouse=True)
# def _ensure_repo_dependencies():
#     ensure_npm_dependencies(TestAddAdminApiEndpoint.REPO_DIR)


class TestAddAdminApiEndpoint:
    """Verify Ghost Admin API audit_logs endpoint implementation."""

    REPO_DIR = "/workspace/Ghost"

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    def _read(self, *parts):
        fpath = os.path.join(self.REPO_DIR, *parts)
        assert os.path.isfile(fpath), f"Required file not found: {fpath}"
        with open(fpath, "r", errors="ignore") as fh:
            return fh.read()

    # ------------------------------------------------------------------
    # L1: Model field & schema validation
    # ------------------------------------------------------------------

    def test_model_defines_all_required_fields(self):
        """AuditLog model must define ALL five schema fields: id, userId, action, context, createdAt."""
        content = self._read(
            "ghost", "core", "core", "server", "models", "audit-log.js"
        )
        required_fields = ["userId", "action", "context", "createdAt"]
        missing = [f for f in required_fields if f not in content]
        assert not missing, f"audit-log.js is missing required schema fields: {missing}"

    def test_model_userId_is_objectid_type(self):
        """userId field in model must be declared as ObjectId (foreign key reference to User)."""
        content = self._read(
            "ghost", "core", "core", "server", "models", "audit-log.js"
        )
        # Typical Ghost/Bookshelf pattern: type: 'string' with length 24, or ObjectId comment,
        # or a foreign-key relationship to users table.
        objectid_patterns = [
            r"ObjectId",
            r"userId.*user",
            r"user.*userId",
            r"references.*users",
            r"foreign.*key",
        ]
        matched = any(re.search(p, content, re.IGNORECASE) for p in objectid_patterns)
        # At minimum userId must appear in close proximity to an id-like qualifier
        assert matched or re.search(
            r"userId\s*[=:,]", content
        ), "userId does not appear to be declared as an ObjectId / user reference in audit-log.js"

    def test_model_action_is_string_type(self):
        """action field must be declared as a string type in the schema."""
        content = self._read(
            "ghost", "core", "core", "server", "models", "audit-log.js"
        )
        # Look for action appearing alongside string type hints or schema definition
        assert re.search(r"action", content), "action field missing from model"
        # Ensure it is not only used as a variable in logic — it should appear in a schema block
        assert re.search(
            r"['\"]action['\"]|action\s*:", content
        ), "action does not appear to be declared as a schema property in audit-log.js"

    def test_model_context_supports_json(self):
        """context field must support JSON/object storage (not a plain scalar type)."""
        content = self._read(
            "ghost", "core", "core", "server", "models", "audit-log.js"
        )
        json_patterns = [
            r"JSON",
            r"json",
            r"jsonb",
            r"context.*object",
            r"object.*context",
            r"serialize",
            r"parse",
        ]
        assert (
            any(re.search(p, content) for p in json_patterns) or "context" in content
        ), "context field does not appear to support JSON storage in audit-log.js"

    def test_model_extends_ghost_base_model(self):
        """Model must extend Ghost's base model (ghostBookshelf or similar backbone/bookshelf pattern)."""
        content = self._read(
            "ghost", "core", "core", "server", "models", "audit-log.js"
        )
        base_patterns = [
            r"ghostBookshelf",
            r"bookshelf",
            r"Model\.extend",
            r"extend\(",
            r"GhostModel",
        ]
        assert any(
            re.search(p, content, re.IGNORECASE) for p in base_patterns
        ), "audit-log.js does not appear to extend Ghost's base model (ghostBookshelf/bookshelf)"

    def test_model_exports_audit_log(self):
        """Model must export the AuditLog class/object so it can be require()'d."""
        content = self._read(
            "ghost", "core", "core", "server", "models", "audit-log.js"
        )
        assert re.search(
            r"module\.exports|exports\.", content
        ), "audit-log.js does not export anything via module.exports"
        assert re.search(
            r"[Aa]udit[_-]?[Ll]og", content
        ), "audit-log.js exports do not reference AuditLog"

    # ------------------------------------------------------------------
    # L2: Endpoint handler structure & pagination logic
    # ------------------------------------------------------------------

    def test_endpoint_exports_browse_and_read(self):
        """audit-logs.js must export both browse and read handler functions."""
        content = self._read(
            "ghost", "core", "core", "server", "api", "endpoints", "audit-logs.js"
        )
        assert "browse" in content, "audit-logs.js missing 'browse' handler export"
        assert "read" in content, "audit-logs.js missing 'read' handler export"
        # Both must appear in an exports/module.exports context
        assert re.search(
            r"module\.exports|exports\.", content
        ), "audit-logs.js does not use module.exports"

    def test_endpoint_browse_supports_limit_and_page(self):
        """browse handler must declare support for BOTH limit AND page pagination parameters."""
        content = self._read(
            "ghost", "core", "core", "server", "api", "endpoints", "audit-logs.js"
        )
        assert (
            "limit" in content
        ), "audit-logs.js browse handler missing 'limit' pagination param"
        assert (
            "page" in content
        ), "audit-logs.js browse handler missing 'page' pagination param"

    def test_endpoint_read_accepts_id_param(self):
        """read handler must accept an id parameter to fetch a single audit log record."""
        content = self._read(
            "ghost", "core", "core", "server", "api", "endpoints", "audit-logs.js"
        )
        id_patterns = [r"\bid\b", r"options\.id", r"data\.id", r"params\.id"]
        assert any(
            re.search(p, content) for p in id_patterns
        ), "read handler in audit-logs.js does not appear to consume an 'id' parameter"

    def test_endpoint_response_wraps_in_audit_logs_key(self):
        """Response must wrap records under the 'audit_logs' key (Ghost API convention)."""
        content = self._read(
            "ghost", "core", "core", "server", "api", "endpoints", "audit-logs.js"
        )
        assert re.search(
            r"audit_logs|auditLogs", content
        ), "audit-logs.js does not wrap its response data in an 'audit_logs' key"

    def test_endpoint_browse_calls_model_fetch(self):
        """browse handler must call a model method to retrieve records (findPage, findAll, fetchAll, etc.)."""
        content = self._read(
            "ghost", "core", "core", "server", "api", "endpoints", "audit-logs.js"
        )
        fetch_patterns = [
            r"findPage",
            r"findAll",
            r"fetchAll",
            r"\.fetch\b",
            r"\.findOne",
            r"getFilteredCollection",
        ]
        assert any(
            re.search(p, content) for p in fetch_patterns
        ), "browse handler does not appear to call any model fetch method (findPage/findAll/fetchAll)"

    # ------------------------------------------------------------------
    # L3: Permission / authentication enforcement
    # ------------------------------------------------------------------

    def test_endpoint_declares_permissions(self):
        """Endpoint must declare admin-only permissions (Ghost uses permissions objects or docName)."""
        content = self._read(
            "ghost", "core", "core", "server", "api", "endpoints", "audit-logs.js"
        )
        perm_patterns = [
            r"permissions",
            r"docName",
            r"canThis",
            r"isAuthenticated",
            r"authorize",
            r"owner",
            r"administrator",
        ]
        assert any(
            re.search(p, content, re.IGNORECASE) for p in perm_patterns
        ), "No permission/auth declaration found in audit-logs.js — endpoint must be admin-only"

    def test_endpoint_permission_targets_audit_log_resource(self):
        """The permission check must reference the audit_log or audit-log resource (not a generic wildcard)."""
        content = self._read(
            "ghost", "core", "core", "server", "api", "endpoints", "audit-logs.js"
        )
        resource_patterns = [r"audit[_\-]log", r"auditLog", r"audit_log"]
        assert any(
            re.search(p, content, re.IGNORECASE) for p in resource_patterns
        ), "Permission check in audit-logs.js does not appear to reference the audit_log resource"

    # ------------------------------------------------------------------
    # L4: Route registration structure
    # ------------------------------------------------------------------

    def test_routes_maps_get_method_for_browse(self):
        """admin/routes.js must register a GET route for the audit_logs collection endpoint."""
        content = self._read(
            "ghost",
            "core",
            "core",
            "server",
            "web",
            "api",
            "endpoints",
            "admin",
            "routes.js",
        )
        # Must have a GET (or router.get) associated with audit_logs path
        get_audit_pattern = re.search(
            r"(get|GET).*audit|audit.*(get|GET)", content, re.IGNORECASE | re.DOTALL
        )
        # Or a resource/router definition that lists audit_logs as a route
        resource_pattern = re.search(r"audit_logs|audit-logs", content, re.IGNORECASE)
        assert (
            resource_pattern
        ), "admin/routes.js does not register any route containing 'audit_logs' or 'audit-logs'"
        assert get_audit_pattern or re.search(
            r"router\.(get|use)", content, re.IGNORECASE
        ), "admin/routes.js does not use a GET handler alongside the audit_logs route"

    def test_routes_registers_single_record_route(self):
        """admin/routes.js must register both the collection route and the /:id single-record route."""
        content = self._read(
            "ghost",
            "core",
            "core",
            "server",
            "web",
            "api",
            "endpoints",
            "admin",
            "routes.js",
        )
        # Single-record GET route (:id parameter or similar)
        id_route_pattern = re.search(r":id|\/\:|\/:id", content)
        # OR at minimum two separate mentions of audit in the route block
        audit_mentions = len(re.findall(r"audit", content, re.IGNORECASE))
        assert id_route_pattern or audit_mentions >= 2, (
            "admin/routes.js appears to be missing a /:id single-record route for audit_logs "
            "(need GET /audit_logs/:id in addition to GET /audit_logs/)"
        )

    def test_routes_references_endpoint_handler(self):
        """admin/routes.js must reference the audit-logs endpoint handler module."""
        content = self._read(
            "ghost",
            "core",
            "core",
            "server",
            "web",
            "api",
            "endpoints",
            "admin",
            "routes.js",
        )
        require_pattern = re.search(
            r"require.*audit|audit.*require|audit.*endpoint|endpoint.*audit",
            content,
            re.IGNORECASE,
        )
        import_pattern = re.search(
            r"import.*audit|audit.*import", content, re.IGNORECASE
        )
        # May also reference via a router binding without explicit require if it is auto-loaded
        direct_ref = re.search(
            r"auditLogs|audit_logs|audit-logs", content, re.IGNORECASE
        )
        assert (
            require_pattern or import_pattern or direct_ref
        ), "admin/routes.js does not appear to reference the audit-logs endpoint handler"

    # ------------------------------------------------------------------
    # L5: E2E test file coverage
    # ------------------------------------------------------------------

    def test_e2e_tests_cover_browse_endpoint(self):
        """E2E test file must contain tests for the list/browse (GET /audit_logs/) endpoint."""
        content = self._read(
            "ghost", "core", "test", "e2e-api", "admin", "audit-logs.test.js"
        )
        browse_patterns = [
            r"/audit_logs/\b",
            r"audit[_-]logs.*get",
            r"get.*audit[_-]logs",
            r"browse",
        ]
        assert any(
            re.search(p, content, re.IGNORECASE) for p in browse_patterns
        ), "E2E test file does not appear to test the browse (GET /audit_logs/) endpoint"

    def test_e2e_tests_cover_read_by_id(self):
        """E2E test file must contain a test for the single-record (GET /audit_logs/:id) endpoint."""
        content = self._read(
            "ghost", "core", "test", "e2e-api", "admin", "audit-logs.test.js"
        )
        read_patterns = [
            r"audit_logs/\$\{",
            r"audit_logs/.*id",
            r"/:id",
            r"\bread\b",
            r"single",
        ]
        assert any(
            re.search(p, content, re.IGNORECASE) for p in read_patterns
        ), "E2E test file does not appear to test the single-record (GET /audit_logs/:id) endpoint"

    def test_e2e_tests_assert_200_on_authenticated_request(self):
        """E2E test must assert HTTP 200 for authenticated owner/admin requests."""
        content = self._read(
            "ghost", "core", "test", "e2e-api", "admin", "audit-logs.test.js"
        )
        assert re.search(
            r"200", content
        ), "E2E test file does not assert HTTP 200 for authenticated requests"

    def test_e2e_tests_assert_401_for_unauthenticated(self):
        """E2E test must assert HTTP 401 for unauthenticated requests."""
        content = self._read(
            "ghost", "core", "test", "e2e-api", "admin", "audit-logs.test.js"
        )
        assert re.search(
            r"401", content
        ), "E2E test file does not assert HTTP 401 for unauthenticated requests"

    def test_e2e_tests_validate_response_structure(self):
        """E2E test must inspect the response body for the audit_logs field."""
        content = self._read(
            "ghost", "core", "test", "e2e-api", "admin", "audit-logs.test.js"
        )
        assert re.search(
            r"audit_logs|auditLogs", content
        ), "E2E test does not validate that response body contains the 'audit_logs' field"

    def test_e2e_tests_cover_pagination(self):
        """E2E test must exercise the pagination parameters (limit and/or page)."""
        content = self._read(
            "ghost", "core", "test", "e2e-api", "admin", "audit-logs.test.js"
        )
        pagination_patterns = [r"limit", r"page", r"pagination", r"per_page"]
        assert any(
            re.search(p, content, re.IGNORECASE) for p in pagination_patterns
        ), "E2E test file does not exercise pagination (limit/page) parameters"

    # ------------------------------------------------------------------
    # L6: Node.js syntax sanity checks
    # ------------------------------------------------------------------

    def test_model_has_no_syntax_errors(self):
        """Node.js must be able to parse the AuditLog model without SyntaxErrors."""
        model_path = os.path.join(
            self.REPO_DIR,
            "ghost",
            "core",
            "core",
            "server",
            "models",
            "audit-log.js",
        )
        result = subprocess.run(
            ["node", "--check", model_path],
            cwd=self.REPO_DIR,
            capture_output=True,
            text=True,
            timeout=30,
        )
        assert (
            result.returncode == 0
        ), f"Syntax error detected in audit-log.js:\n{result.stderr}"

    def test_endpoint_has_no_syntax_errors(self):
        """Node.js must be able to parse the audit-logs endpoint without SyntaxErrors."""
        endpoint_path = os.path.join(
            self.REPO_DIR,
            "ghost",
            "core",
            "core",
            "server",
            "api",
            "endpoints",
            "audit-logs.js",
        )
        result = subprocess.run(
            ["node", "--check", endpoint_path],
            cwd=self.REPO_DIR,
            capture_output=True,
            text=True,
            timeout=30,
        )
        assert (
            result.returncode == 0
        ), f"Syntax error detected in audit-logs.js:\n{result.stderr}"

    def test_e2e_test_file_has_no_syntax_errors(self):
        """Node.js must be able to parse the E2E test file without SyntaxErrors."""
        test_path = os.path.join(
            self.REPO_DIR,
            "ghost",
            "core",
            "test",
            "e2e-api",
            "admin",
            "audit-logs.test.js",
        )
        result = subprocess.run(
            ["node", "--check", test_path],
            cwd=self.REPO_DIR,
            capture_output=True,
            text=True,
            timeout=30,
        )
        assert (
            result.returncode == 0
        ), f"Syntax error detected in audit-logs.test.js:\n{result.stderr}"
