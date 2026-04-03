"""
Test for 'mcp-builder' skill — MCP Server Builder
Validates MCP server TypeScript project structure: server.ts, registry.ts,
protocol.ts, JSON-RPC error codes, tools/list method, TypeScript compilation,
and Jest test execution.
"""

import glob
import json
import os
import re
import subprocess

import pytest


class TestMcpBuilder:
    """Verify MCP Server Builder project structure and behavior."""

    REPO_DIR = "/workspace/servers"
    PKG_DIR = os.path.join(REPO_DIR, "packages", "mcp-builder")

    # ── helpers ──────────────────────────────────────────────────────────
    @staticmethod
    def _read_file(path: str) -> str:
        try:
            with open(path, "r", errors="ignore") as fh:
                return fh.read()
        except OSError:
            return ""

    @classmethod
    def _npm_install(cls):
        result = subprocess.run(
            ["npm", "install"], cwd=cls.PKG_DIR, capture_output=True, timeout=120
        )
        if result.returncode != 0:
            pytest.skip("npm install failed in mcp-builder")

    # ── file_path_check ──────────────────────────────────────────────────

    def test_server_ts_exists(self):
        """packages/mcp-builder/src/server.ts must exist and be non-empty."""
        path = os.path.join(self.PKG_DIR, "src", "server.ts")
        assert os.path.isfile(path), f"{path} does not exist"
        assert os.path.getsize(path) > 0, "server.ts is empty"

    def test_registry_and_protocol_ts_exist(self):
        """registry.ts and protocol.ts must exist."""
        for name in ("registry.ts", "protocol.ts"):
            path = os.path.join(self.PKG_DIR, "src", name)
            assert os.path.isfile(path), f"{path} does not exist"
            assert os.path.getsize(path) > 0, f"{name} is empty"

    def test_package_json_and_test_file_exist(self):
        """package.json with jest config and __tests__/server.test.ts must exist."""
        pkg_path = os.path.join(self.PKG_DIR, "package.json")
        assert os.path.isfile(pkg_path), f"{pkg_path} does not exist"
        with open(pkg_path) as f:
            pkg = json.load(f)
        has_jest = (
            "jest" in pkg
            or "jest" in pkg.get("devDependencies", {})
            or "jest" in pkg.get("dependencies", {})
            or "jest" in str(pkg.get("scripts", {}))
        )
        assert has_jest, "package.json has no jest configuration"
        test_path = os.path.join(self.PKG_DIR, "src", "__tests__", "server.test.ts")
        assert os.path.isfile(test_path), f"{test_path} does not exist"

    # ── semantic_check ───────────────────────────────────────────────────

    def test_tools_list_method_defined_in_server(self):
        """server.ts must define tools/list handler or listTools method."""
        content = self._read_file(os.path.join(self.PKG_DIR, "src", "server.ts"))
        patterns = ["tools/list", "tools\\\\list", "listTools", "tools_list"]
        found = any(p in content for p in patterns)
        assert found, "tools/list handler not defined in server.ts"

    def test_jsonrpc_error_codes_defined_in_protocol(self):
        """-32601 (MethodNotFound) and -32602 (InvalidParams) must be defined."""
        content = self._read_file(os.path.join(self.PKG_DIR, "src", "protocol.ts"))
        assert "-32601" in content, "Error code -32601 (MethodNotFound) not defined"
        assert "-32602" in content, "Error code -32602 (InvalidParams) not defined"

    def test_jsonrpc_responses_include_version_and_id(self):
        """Protocol must set jsonrpc:'2.0' and echo request id in responses."""
        content = self._read_file(os.path.join(self.PKG_DIR, "src", "protocol.ts"))
        assert "2.0" in content, "JSON-RPC version '2.0' not found in protocol.ts"
        assert "id" in content, "'id' field not referenced in protocol.ts"

    def test_initialize_returns_server_capabilities(self):
        """server.ts must define initialize handler with serverInfo/capabilities."""
        content = self._read_file(os.path.join(self.PKG_DIR, "src", "server.ts"))
        assert "initialize" in content, "'initialize' method not found in server.ts"
        has_caps = "serverInfo" in content or "capabilities" in content
        assert has_caps, "serverInfo/capabilities not returned by initialize"

    # ── functional_check (command) ───────────────────────────────────────

    def test_typescript_compilation_no_errors(self):
        """npx tsc --noEmit must pass without errors."""
        self._npm_install()
        result = subprocess.run(
            ["npx", "tsc", "--noEmit"],
            cwd=self.PKG_DIR,
            capture_output=True,
            timeout=120,
        )
        assert result.returncode == 0, (
            f"tsc --noEmit failed: {result.stderr.decode(errors='replace')[:500]}"
        )

    def test_tools_list_returns_array_of_tool_definitions(self):
        """Jest test for tools/list must pass."""
        self._npm_install()
        result = subprocess.run(
            ["npx", "jest", "--testNamePattern", "tools/list"],
            cwd=self.PKG_DIR,
            capture_output=True,
            timeout=120,
        )
        assert result.returncode == 0, (
            f"tools/list Jest test failed: {result.stdout.decode(errors='replace')[:500]}"
        )

    def test_tools_call_valid_tool_returns_content(self):
        """Jest test for tools/call with valid tool must pass."""
        self._npm_install()
        result = subprocess.run(
            ["npx", "jest", "--testNamePattern", "tools/call.*valid"],
            cwd=self.PKG_DIR,
            capture_output=True,
            timeout=120,
        )
        assert result.returncode == 0, (
            f"tools/call jest test failed: {result.stdout.decode(errors='replace')[:500]}"
        )

    def test_unknown_tool_returns_method_not_found(self):
        """Jest test for unknown tool (-32601) must pass."""
        self._npm_install()
        result = subprocess.run(
            ["npx", "jest", "--testNamePattern", "unknown|MethodNotFound"],
            cwd=self.PKG_DIR,
            capture_output=True,
            timeout=120,
        )
        assert result.returncode == 0, (
            f"MethodNotFound jest test failed: {result.stdout.decode(errors='replace')[:500]}"
        )

    def test_invalid_args_returns_invalid_params(self):
        """Jest test for invalid args (-32602) must pass."""
        self._npm_install()
        result = subprocess.run(
            ["npx", "jest", "--testNamePattern", "invalid.*args|InvalidParams"],
            cwd=self.PKG_DIR,
            capture_output=True,
            timeout=120,
        )
        assert result.returncode == 0, (
            f"InvalidParams jest test failed: {result.stdout.decode(errors='replace')[:500]}"
        )

    def test_double_tool_registration_handled(self):
        """registry.ts must handle duplicate tool registration."""
        content = self._read_file(os.path.join(self.PKG_DIR, "src", "registry.ts"))
        patterns = ["duplicate", "already", "has(", "throw", "overwrite", "existing"]
        found = any(p in content.lower() for p in patterns)
        assert found, "No duplicate tool registration handling in registry.ts"
