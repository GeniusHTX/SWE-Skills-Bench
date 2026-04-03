"""Test file for the add-admin-api-endpoint skill.

This suite validates the Ghost newsletters bulk admin endpoint files,
route registration, and endpoint behavior with mocked service dependencies.
"""

from __future__ import annotations

import json
import pathlib
import re
import shutil
import subprocess
import tempfile
import textwrap

import pytest


class TestAddAdminApiEndpoint:
    """Verify the Ghost admin newsletters bulk endpoint implementation."""

    REPO_DIR = "/workspace/Ghost"
    _setup_attempted = False
    _setup_ok = False
    _setup_reason = ""

    def _repo_path(self, relative_path: str) -> pathlib.Path:
        return pathlib.Path(self.REPO_DIR, *relative_path.split("/"))

    def _core_dir(self) -> pathlib.Path:
        return self._repo_path("ghost/core")

    def _read_text(self, relative_path: str) -> str:
        path = self._repo_path(relative_path)
        assert path.exists(), f"Expected path to exist: {path}"
        return path.read_text(encoding="utf-8", errors="ignore")

    def _assert_non_empty_file(self, relative_path: str) -> pathlib.Path:
        path = self._repo_path(relative_path)
        assert path.is_file(), f"Expected file to exist: {path}"
        assert path.stat().st_size > 0, f"Expected file to be non-empty: {path}"
        return path

    @classmethod
    def _ensure_optional_setup(cls) -> None:
        if cls._setup_attempted:
            if not cls._setup_ok:
                pytest.skip(cls._setup_reason)
            return
        cls._setup_attempted = True
        npm = shutil.which("npm")
        node = shutil.which("node")
        if not npm or not node:
            cls._setup_reason = (
                "Skipping Node-dependent test because node/npm is unavailable"
            )
            pytest.skip(cls._setup_reason)
        result = subprocess.run(
            [npm, "install"],
            cwd=pathlib.Path(cls.REPO_DIR, "ghost", "core"),
            capture_output=True,
            text=True,
            timeout=300,
        )
        if result.returncode != 0:
            cls._setup_reason = (
                "Skipping Node-dependent test because npm install failed.\n"
                f"stdout:\n{result.stdout}\n"
                f"stderr:\n{result.stderr}"
            )
            pytest.skip(cls._setup_reason)
        cls._setup_ok = True

    def _run_node_json(self, source: str, timeout: int = 120) -> dict:
        node = shutil.which("node")
        assert node, "Expected node to be available for Ghost endpoint tests"
        with tempfile.NamedTemporaryFile(
            "w", suffix=".js", delete=False, encoding="utf-8"
        ) as handle:
            handle.write(source)
            temp_path = pathlib.Path(handle.name)
        try:
            result = subprocess.run(
                [node, str(temp_path)],
                cwd=self._core_dir(),
                capture_output=True,
                text=True,
                timeout=timeout,
            )
        finally:
            temp_path.unlink(missing_ok=True)
        assert result.returncode == 0, (
            "Expected Node script to succeed.\n"
            f"stdout:\n{result.stdout}\n"
            f"stderr:\n{result.stderr}"
        )
        stdout = result.stdout.strip()
        assert stdout, "Expected Node script to emit JSON output"
        return json.loads(stdout)

    def _extract_items(self, payload: object) -> list[dict]:
        if isinstance(payload, list):
            return [item for item in payload if isinstance(item, dict)]
        if isinstance(payload, dict):
            for key in ("newsletters", "bulk", "data", "results"):
                value = payload.get(key)
                if isinstance(value, list):
                    return [item for item in value if isinstance(item, dict)]
            for value in payload.values():
                items = self._extract_items(value)
                if items:
                    return items
        return []

    def _run_endpoint_case(
        self,
        action: str,
        bulk: list[dict],
        response_items: list[dict] | None = None,
        error_status: int | None = None,
    ) -> dict:
        self._ensure_optional_setup()
        endpoint_path = self._repo_path(
            "ghost/core/core/server/api/endpoints/newsletters-bulk.js"
        )
        scenario = {
            "action": action,
            "bulk": bulk,
            "response_items": response_items or [],
            "error_status": error_status,
        }
        source = textwrap.dedent(
            f"""
            const Module = require("module");
            const scenario = {json.dumps(scenario)};
            const endpointPath = {json.dumps(str(endpoint_path))};
            const calls = [];

            class FakeNewsletterBulkService {{
              async archive(items) {{
                calls.push({{ method: "archive", items }});
                if (scenario.error_status) {{
                  throw Object.assign(new Error("archive failed"), {{ statusCode: scenario.error_status }});
                }}
                return scenario.response_items.length ? scenario.response_items : items.map((item, index) => ({{
                  id: item.id || `archive-${{index}}`,
                  status: "archived",
                  visibility: "none",
                  action: item.action,
                }}));
              }}

              async unarchive(items) {{
                calls.push({{ method: "unarchive", items }});
                if (scenario.error_status) {{
                  throw Object.assign(new Error("unarchive failed"), {{ statusCode: scenario.error_status }});
                }}
                return scenario.response_items.length ? scenario.response_items : items.map((item, index) => ({{
                  id: item.id || `unarchive-${{index}}`,
                  status: "active",
                  visibility: "members",
                  action: item.action,
                }}));
              }}

              async reorder(items) {{
                calls.push({{ method: "reorder", items }});
                if (scenario.error_status) {{
                  throw Object.assign(new Error("reorder failed"), {{ statusCode: scenario.error_status }});
                }}
                return scenario.response_items.length ? scenario.response_items : items.map((item) => ({{
                  id: item.id,
                  sort_order: item.sort_order,
                  action: item.action,
                }}));
              }}

              async edit(items) {{
                const action = (items?.[0]?.action) || scenario.action;
                if (typeof this[action] !== "function") {{
                  throw Object.assign(new Error(`Unsupported action: ${{action}}`), {{ statusCode: 500 }});
                }}
                return this[action](items);
              }}

              async bulkEdit(items) {{
                return this.edit(items);
              }}
            }}

            const fakeModule = FakeNewsletterBulkService;
            fakeModule.default = FakeNewsletterBulkService;
            fakeModule.NewsletterBulkService = FakeNewsletterBulkService;

            function resolveHandler(mod) {{
              const candidates = [
                mod,
                mod.put,
                mod.edit,
                mod.default,
                mod.default && mod.default.put,
                mod.default && mod.default.edit,
                mod.newslettersBulk,
                mod.newslettersBulk && mod.newslettersBulk.put,
                mod.newslettersBulk && mod.newslettersBulk.edit,
              ];
              for (const candidate of candidates) {{
                if (typeof candidate === "function") {{
                  return candidate;
                }}
              }}
              return null;
            }}

            async function main() {{
              const originalLoad = Module._load;
              Module._load = function(request, parent, isMain) {{
                if (request.includes("NewsletterBulkService")) {{
                  return fakeModule;
                }}
                return originalLoad.apply(this, arguments);
              }};

              try {{
                const endpointModule = require(endpointPath);
                const handler = resolveHandler(endpointModule);
                if (!handler) {{
                  throw new Error("Could not resolve newsletters bulk handler export");
                }}

                const bulk = scenario.bulk;
                const req = {{ body: {{ bulk }}, user: {{ id: "admin-user", role: "Owner" }} }};
                const frame = {{
                  body: {{ bulk }},
                  data: {{ bulk }},
                  payload: {{ bulk }},
                  req,
                  request: req,
                  original: {{ req }},
                  options: {{ data: {{ bulk }}, context: {{ user: req.user }} }},
                }};

                try {{
                  const result = await Promise.resolve(handler(frame));
                  console.log(JSON.stringify({{ ok: true, calls, result }}));
                }} catch (error) {{
                  console.log(JSON.stringify({{
                    ok: false,
                    calls,
                    error: {{
                      message: error && error.message ? error.message : String(error),
                      statusCode: error && (error.statusCode || error.status) ? (error.statusCode || error.status) : null,
                    }},
                  }}));
                }}
              }} finally {{
                Module._load = originalLoad;
              }}
            }}

            main().catch((error) => {{
              console.error(error && error.stack ? error.stack : String(error));
              process.exit(1);
            }});
            """
        )
        return self._run_node_json(source)

    def test_file_path_ghost_core_core_server_api_endpoints_newsletters_bulk_js_exi(
        self,
    ) -> None:
        """Verify that the newsletters bulk endpoint file exists in the expected Ghost API directory."""
        self._assert_non_empty_file(
            "ghost/core/core/server/api/endpoints/newsletters-bulk.js"
        )

    def test_file_path_ghost_core_core_server_services_newsletters_newsletterbulkse(
        self,
    ) -> None:
        """Verify that the newsletters bulk service file exists in the expected Ghost service directory."""
        self._assert_non_empty_file(
            "ghost/core/core/server/services/newsletters/NewsletterBulkService.js"
        )

    def test_file_path_ghost_core_core_server_web_api_endpoints_admin_middleware_js(
        self,
    ) -> None:
        """Verify that the Ghost admin middleware file exists and references the newsletters bulk route registration."""
        path = self._assert_non_empty_file(
            "ghost/core/core/server/web/api/endpoints/admin/middleware.js"
        )
        content = path.read_text(encoding="utf-8", errors="ignore")
        assert re.search(
            r"newsletters\s*/\s*bulk|newsletters-bulk|/newsletters/bulk/?", content
        ), "Expected Ghost admin middleware to mention the newsletters bulk route"

    def test_semantic_newsletters_bulk_js_exports_a_put_handler_that_parses_the_bu(
        self,
    ) -> None:
        """Verify that the endpoint module exposes a writable handler and pulls a bulk array from request data."""
        content = self._read_text(
            "ghost/core/core/server/api/endpoints/newsletters-bulk.js"
        )
        assert re.search(
            r"\b(?:put|edit)\b", content
        ), "Expected the endpoint file to expose a PUT-style handler"
        assert re.search(
            r"\bbulk\b", content
        ), "Expected the endpoint file to reference a bulk payload"
        assert re.search(
            r"(?:body|req\.body|data|payload).*bulk", content, re.DOTALL
        ), "Expected the endpoint file to read bulk data from the request payload"

    def test_semantic_newsletterbulkservice_js_contains_methods_for_archive_unarch(
        self,
    ) -> None:
        """Verify that the service implements archive, unarchive, and reorder operations with validation-aware structure."""
        content = self._read_text(
            "ghost/core/core/server/services/newsletters/NewsletterBulkService.js"
        )
        methods = set(re.findall(r"\b(archive|unarchive|reorder)\b", content))
        assert methods == {
            "archive",
            "reorder",
            "unarchive",
        }, f"Expected archive/unarchive/reorder methods, got: {sorted(methods)}"
        assert re.search(
            r"(?:validate|invalid|error|throw)", content
        ), "Expected the service to contain explicit validation or error handling logic"

    def test_semantic_middleware_js_registers_newsletters_bulk_route_in_admin_api_(
        self,
    ) -> None:
        """Verify that the admin middleware registers a newsletters bulk route on the admin API router."""
        content = self._read_text(
            "ghost/core/core/server/web/api/endpoints/admin/middleware.js"
        )
        assert re.search(
            r"router|apiRouter|adminRouter", content
        ), "Expected an admin router to be present"
        assert re.search(
            r"/newsletters/bulk/?", content
        ), "Expected the newsletters bulk route to be registered"
        assert re.search(
            r"\.(?:put|route|use)\(", content
        ), "Expected the route to be attached through router configuration"

    def test_semantic_validation_logic_checks_uuid_format_recognized_actions_sort_(
        self,
    ) -> None:
        """Verify that validation logic checks item identity, action values, and sort_order constraints."""
        endpoint_content = self._read_text(
            "ghost/core/core/server/api/endpoints/newsletters-bulk.js"
        )
        service_content = self._read_text(
            "ghost/core/core/server/services/newsletters/NewsletterBulkService.js"
        )
        combined = endpoint_content + "\n" + service_content
        assert re.search(
            r"(?:uuid|isUUID|[0-9a-f]{{8}}-[0-9a-f]{{4}}-[0-9a-f]{{4}}-[0-9a-f]{{4}}-[0-9a-f]{{12}})",
            combined,
            re.IGNORECASE,
        ), "Expected validation logic for newsletter identifiers"
        assert {"archive", "unarchive", "reorder"}.issubset(
            set(re.findall(r"\b(archive|unarchive|reorder)\b", combined))
        ), "Expected validation logic to enumerate recognized actions"
        assert re.search(
            r"sort_order", combined
        ), "Expected reorder validation to reference sort_order"
        assert re.search(
            r"(?:<\s*0|negative|>=\s*0|Number\.isInteger)", combined
        ), "Expected reorder validation to constrain sort_order values"

    def test_semantic_atomicity_implemented_via_transaction_or_rollback_pattern(
        self,
    ) -> None:
        """Verify that bulk updates are wrapped in a transaction or an explicit rollback-aware control flow."""
        endpoint_content = self._read_text(
            "ghost/core/core/server/api/endpoints/newsletters-bulk.js"
        )
        service_content = self._read_text(
            "ghost/core/core/server/services/newsletters/NewsletterBulkService.js"
        )
        combined = endpoint_content + "\n" + service_content
        assert re.search(
            r"(?:transaction|transacting|rollback|commit)", combined
        ), "Expected the bulk implementation to use a transaction or rollback pattern"

    def test_functional_valid_archive_request_returns_http_200_with_status_archived_(
        self,
    ) -> None:
        """Verify that a valid archive bulk request delegates the archive action and returns archived newsletter objects."""
        payload = self._run_endpoint_case(
            action="archive",
            bulk=[
                {"id": "00000000-0000-0000-0000-000000000001", "action": "archive"},
                {"id": "00000000-0000-0000-0000-000000000002", "action": "archive"},
            ],
            response_items=[
                {
                    "id": "00000000-0000-0000-0000-000000000001",
                    "status": "archived",
                    "visibility": "none",
                },
                {
                    "id": "00000000-0000-0000-0000-000000000002",
                    "status": "archived",
                    "visibility": "none",
                },
            ],
        )
        assert payload["ok"] is True, payload
        assert payload["calls"] and payload["calls"][0]["method"] == "archive", payload
        items = self._extract_items(payload.get("result", {}))
        assert len(items) == 2, payload
        assert {item.get("status") for item in items} == {"archived"}, payload
        assert {item.get("visibility") for item in items} == {"none"}, payload

    def test_functional_valid_unarchive_request_returns_http_200_with_status_active_(
        self,
    ) -> None:
        """Verify that a valid unarchive request delegates the unarchive action and returns active newsletter objects."""
        payload = self._run_endpoint_case(
            action="unarchive",
            bulk=[
                {"id": "00000000-0000-0000-0000-000000000003", "action": "unarchive"}
            ],
            response_items=[
                {
                    "id": "00000000-0000-0000-0000-000000000003",
                    "status": "active",
                    "visibility": "members",
                }
            ],
        )
        assert payload["ok"] is True, payload
        assert (
            payload["calls"] and payload["calls"][0]["method"] == "unarchive"
        ), payload
        items = self._extract_items(payload.get("result", {}))
        assert len(items) == 1, payload
        assert items[0].get("status") == "active", payload
        assert items[0].get("visibility") == "members", payload

    def test_functional_valid_reorder_request_returns_http_200_with_updated_sort_ord(
        self,
    ) -> None:
        """Verify that a valid reorder request delegates the reorder action and returns updated sort_order values."""
        payload = self._run_endpoint_case(
            action="reorder",
            bulk=[
                {
                    "id": "00000000-0000-0000-0000-000000000004",
                    "action": "reorder",
                    "sort_order": 0,
                },
                {
                    "id": "00000000-0000-0000-0000-000000000005",
                    "action": "reorder",
                    "sort_order": 1,
                },
            ],
            response_items=[
                {"id": "00000000-0000-0000-0000-000000000004", "sort_order": 0},
                {"id": "00000000-0000-0000-0000-000000000005", "sort_order": 1},
            ],
        )
        assert payload["ok"] is True, payload
        assert payload["calls"] and payload["calls"][0]["method"] == "reorder", payload
        items = self._extract_items(payload.get("result", {}))
        assert [item.get("sort_order") for item in items] == [0, 1], payload

    def test_functional_non_existent_newsletter_id_returns_http_404(self) -> None:
        """Verify that a missing newsletter results in a 404-style failure outcome instead of a silent success."""
        payload = self._run_endpoint_case(
            action="archive",
            bulk=[{"id": "00000000-0000-0000-0000-000000000099", "action": "archive"}],
            error_status=404,
        )
        assert payload["ok"] is False, payload
        assert payload["calls"] and payload["calls"][0]["method"] == "archive", payload
        assert payload["error"]["statusCode"] == 404, payload

    def test_functional_empty_bulk_array_returns_http_422(self) -> None:
        """Verify that an invalid empty bulk payload produces a 422-style validation failure."""
        payload = self._run_endpoint_case(action="archive", bulk=[], error_status=422)
        assert payload["ok"] is False, payload
        assert payload["error"]["statusCode"] == 422, payload
