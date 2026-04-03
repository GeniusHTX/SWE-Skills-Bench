"""
Test for 'mcp-builder' skill — MCP server implementation
Validates that the Agent built an MCP (Model Context Protocol) server
in the servers repository.
"""

import os
import re

import pytest


class TestMcpBuilder:
    """Verify MCP server implementation."""

    REPO_DIR = "/workspace/servers"

    def test_server_entry_point_exists(self):
        """Server entry point file must exist."""
        found = False
        for root, dirs, files in os.walk(self.REPO_DIR):
            for f in files:
                if f.endswith((".py", ".ts", ".js")):
                    path = os.path.join(root, f)
                    with open(path, "r", errors="ignore") as fh:
                        content = fh.read()
                    if re.search(r"server|Server|MCP|mcp", content):
                        if re.search(r"listen|start|main|run|serve", content):
                            found = True
                            break
            if found:
                break
        assert found, "Server entry point not found"

    def test_tool_definitions(self):
        """MCP server must define tools."""
        found = False
        for root, dirs, files in os.walk(self.REPO_DIR):
            for f in files:
                if f.endswith((".py", ".ts", ".js", ".json")):
                    path = os.path.join(root, f)
                    with open(path, "r", errors="ignore") as fh:
                        content = fh.read()
                    if re.search(r"tool|Tool|tools", content):
                        if re.search(r"name|description|input_schema|parameters", content):
                            found = True
                            break
            if found:
                break
        assert found, "No tool definitions found"

    def test_resource_definitions(self):
        """MCP server should define resources."""
        found = False
        for root, dirs, files in os.walk(self.REPO_DIR):
            for f in files:
                if f.endswith((".py", ".ts", ".js")):
                    path = os.path.join(root, f)
                    with open(path, "r", errors="ignore") as fh:
                        content = fh.read()
                    if re.search(r"resource|Resource|resources", content):
                        if re.search(r"uri|name|description|mimeType|mime_type", content):
                            found = True
                            break
            if found:
                break
        assert found, "No resource definitions found"

    def test_prompt_definitions(self):
        """MCP server should define prompts."""
        found = False
        for root, dirs, files in os.walk(self.REPO_DIR):
            for f in files:
                if f.endswith((".py", ".ts", ".js")):
                    path = os.path.join(root, f)
                    with open(path, "r", errors="ignore") as fh:
                        content = fh.read()
                    if re.search(r"prompt|Prompt|prompts", content):
                        if re.search(r"name|description|argument|message|template", content):
                            found = True
                            break
            if found:
                break
        assert found, "No prompt definitions found"

    def test_handler_for_tool_calls(self):
        """Server must handle tool call requests."""
        found = False
        for root, dirs, files in os.walk(self.REPO_DIR):
            for f in files:
                if f.endswith((".py", ".ts", ".js")):
                    path = os.path.join(root, f)
                    with open(path, "r", errors="ignore") as fh:
                        content = fh.read()
                    if re.search(r"call_tool|handle_tool|tools/call|CallTool|toolCall", content):
                        found = True
                        break
            if found:
                break
        assert found, "No tool call handler found"

    def test_transport_layer(self):
        """Server must implement a transport layer (stdio, HTTP, SSE)."""
        found = False
        for root, dirs, files in os.walk(self.REPO_DIR):
            for f in files:
                if f.endswith((".py", ".ts", ".js")):
                    path = os.path.join(root, f)
                    with open(path, "r", errors="ignore") as fh:
                        content = fh.read()
                    if re.search(r"stdio|StdioServer|SSE|http|transport|stdin|stdout", content, re.IGNORECASE):
                        found = True
                        break
            if found:
                break
        assert found, "No transport layer found"

    def test_mcp_sdk_usage(self):
        """Code should use MCP SDK or protocol implementation."""
        found = False
        for root, dirs, files in os.walk(self.REPO_DIR):
            for f in files:
                if f.endswith((".py", ".ts", ".js")):
                    path = os.path.join(root, f)
                    with open(path, "r", errors="ignore") as fh:
                        content = fh.read()
                    if re.search(r"@modelcontextprotocol|mcp|from mcp|import.*mcp", content, re.IGNORECASE):
                        found = True
                        break
            if found:
                break
        assert found, "No MCP SDK usage found"

    def test_error_handling(self):
        """Server must handle errors gracefully."""
        found = False
        for root, dirs, files in os.walk(self.REPO_DIR):
            for f in files:
                if f.endswith((".py", ".ts", ".js")):
                    path = os.path.join(root, f)
                    with open(path, "r", errors="ignore") as fh:
                        content = fh.read()
                    if re.search(r"server|mcp", content, re.IGNORECASE):
                        if re.search(r"try|catch|except|error|Error|throw", content):
                            found = True
                            break
            if found:
                break
        assert found, "No error handling found"

    def test_schema_validation(self):
        """Tool inputs should have schema validation."""
        found = False
        for root, dirs, files in os.walk(self.REPO_DIR):
            for f in files:
                if f.endswith((".py", ".ts", ".js", ".json")):
                    path = os.path.join(root, f)
                    with open(path, "r", errors="ignore") as fh:
                        content = fh.read()
                    if re.search(r"input_schema|inputSchema|schema|[Zz]od|[Pp]ydantic|properties", content):
                        found = True
                        break
            if found:
                break
        assert found, "No schema validation found"

    def test_readme_or_docs(self):
        """README or documentation must exist."""
        found = False
        for root, dirs, files in os.walk(self.REPO_DIR):
            for f in files:
                if f.lower() in ("readme.md", "readme.rst", "readme.txt", "readme"):
                    found = True
                    break
            if found:
                break
        assert found, "No README found"

    def test_package_config(self):
        """Package configuration (package.json or pyproject.toml) must exist."""
        found = False
        config_files = ["package.json", "pyproject.toml", "setup.py", "setup.cfg"]
        for root, dirs, files in os.walk(self.REPO_DIR):
            for f in files:
                if f in config_files:
                    found = True
                    break
            if found:
                break
        assert found, "No package configuration found"
