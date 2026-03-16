"""
Test for 'mcp-builder' skill — MCP Server Builder
Validates that the Agent created a new MCP (Model Context Protocol) server
implementation with TypeScript source, build config, and tests.
"""

import os
import subprocess
import pytest

from _dependency_utils import ensure_npm_dependencies


@pytest.fixture(scope="module", autouse=True)
def _ensure_repo_dependencies():
    ensure_npm_dependencies(TestMcpBuilder.REPO_DIR)


class TestMcpBuilder:
    """Verify MCP server implementation."""

    REPO_DIR = "/workspace/servers"

    # ------------------------------------------------------------------
    # L1: file existence
    # ------------------------------------------------------------------

    def test_src_directory_exists(self):
        """New server source directory must exist."""
        found = []
        for root, dirs, files in os.walk(self.REPO_DIR):
            for f in files:
                if f.endswith(".ts") and "index" in f.lower():
                    found.append(os.path.join(root, f))
        assert len(found) >= 1, "No TypeScript index.ts found"

    def test_package_json_exists(self):
        """package.json must exist for the server."""
        found = False
        for root, dirs, files in os.walk(self.REPO_DIR):
            if "package.json" in files:
                fpath = os.path.join(root, "package.json")
                with open(fpath, "r") as f:
                    content = f.read()
                if "mcp" in content.lower() or "server" in content.lower():
                    found = True
                    break
        assert found, "No package.json for MCP server found"

    def test_tsconfig_exists(self):
        """tsconfig.json must exist."""
        found = False
        for root, dirs, files in os.walk(self.REPO_DIR):
            if "tsconfig.json" in files:
                found = True
                break
        assert found, "tsconfig.json not found"

    # ------------------------------------------------------------------
    # L2: content & build validation
    # ------------------------------------------------------------------

    def _find_ts_files(self):
        found = []
        for root, dirs, files in os.walk(self.REPO_DIR):
            for f in files:
                if f.endswith(".ts") and "node_modules" not in root:
                    found.append(os.path.join(root, f))
        return found

    def _read_all_ts(self):
        content = ""
        for fpath in self._find_ts_files():
            try:
                with open(fpath, "r", errors="ignore") as f:
                    content += f.read() + "\n"
            except OSError:
                pass
        return content

    def test_mcp_protocol_implementation(self):
        """Source must implement MCP protocol concepts."""
        content = self._read_all_ts()
        mcp_patterns = [
            "Server",
            "Tool",
            "Resource",
            "Prompt",
            "handler",
            "schema",
            "jsonrpc",
        ]
        found = sum(1 for p in mcp_patterns if p in content)
        assert found >= 3, f"Only {found} MCP protocol concepts found"

    def test_tool_definitions(self):
        """Server must define at least one tool."""
        content = self._read_all_ts()
        tool_patterns = [
            "tool",
            "Tool",
            "tools",
            "listTools",
            "callTool",
            "inputSchema",
        ]
        found = sum(1 for p in tool_patterns if p in content)
        assert found >= 2, "Insufficient tool definitions"

    def test_error_handling(self):
        """Server must implement error handling."""
        content = self._read_all_ts()
        error_patterns = ["catch", "Error", "throw", "try", "McpError", "ErrorCode"]
        found = sum(1 for p in error_patterns if p in content)
        assert found >= 2, "Insufficient error handling"

    def test_npm_build(self):
        """npm run build must succeed (find the right package dir)."""
        # Find package.json with build script
        for root, dirs, files in os.walk(self.REPO_DIR):
            if "package.json" in files and "node_modules" not in root:
                import json

                pkg_path = os.path.join(root, "package.json")
                with open(pkg_path, "r") as f:
                    pkg = json.load(f)
                if "build" in pkg.get("scripts", {}):
                    result = subprocess.run(
                        ["npm", "run", "build"],
                        cwd=root,
                        capture_output=True,
                        text=True,
                        timeout=300,
                    )
                    assert (
                        result.returncode == 0
                    ), f"npm build failed in {root}:\n{result.stderr[-1000:]}"
                    return
        pytest.skip("No package.json with build script found")

    def test_input_validation(self):
        """Tools must validate input schemas."""
        content = self._read_all_ts()
        validation_patterns = [
            "schema",
            "zod",
            "Zod",
            "validate",
            "inputSchema",
            "z.object",
            "z.string",
        ]
        found = any(p in content for p in validation_patterns)
        assert found, "No input validation/schema found"

    def test_transport_handling(self):
        """Server must handle transport (stdio or HTTP)."""
        content = self._read_all_ts()
        transport_patterns = [
            "stdio",
            "StdioServerTransport",
            "SSEServerTransport",
            "StreamableHTTPServerTransport",
            "transport",
            "stdin",
            "stdout",
        ]
        found = any(p in content for p in transport_patterns)
        assert found, "No transport handling found"

    def test_exports_or_main(self):
        """Package must have main/exports in package.json."""
        for root, dirs, files in os.walk(self.REPO_DIR):
            if "package.json" in files and "node_modules" not in root:
                import json

                with open(os.path.join(root, "package.json"), "r") as f:
                    pkg = json.load(f)
                if pkg.get("main") or pkg.get("bin") or pkg.get("exports"):
                    return
        pytest.fail("No main/bin/exports field in package.json")
