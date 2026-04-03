"""
Test for 'implementing-jsc-classes-zig' skill — URLPattern Zig/TS bridge in bun
Validates that the Agent implemented the URLPattern class bridging Zig and
TypeScript in the bun runtime.
"""

import os
import re

import pytest


class TestImplementingJscClassesZig:
    """Verify URLPattern Zig/TS bridge in bun."""

    REPO_DIR = "/workspace/bun"

    def test_url_pattern_zig_file_exists(self):
        """A Zig file for URLPattern must exist."""
        found = False
        for root, dirs, files in os.walk(self.REPO_DIR):
            for f in files:
                if f.endswith(".zig"):
                    if "url" in f.lower() and "pattern" in f.lower():
                        found = True
                        break
                    path = os.path.join(root, f)
                    with open(path, "r", errors="ignore") as fh:
                        content = fh.read()
                    if re.search(r"URLPattern", content):
                        found = True
                        break
            if found:
                break
        assert found, "URLPattern Zig file not found"

    def test_url_pattern_typescript_bindings(self):
        """TypeScript bindings or declarations for URLPattern must exist."""
        found = False
        for root, dirs, files in os.walk(self.REPO_DIR):
            for f in files:
                if f.endswith((".ts", ".d.ts")):
                    path = os.path.join(root, f)
                    with open(path, "r", errors="ignore") as fh:
                        content = fh.read()
                    if re.search(r"URLPattern|url_pattern|UrlPattern", content):
                        found = True
                        break
            if found:
                break
        assert found, "URLPattern TypeScript bindings not found"

    def test_jsc_class_definition_in_zig(self):
        """Zig code must define a JSC class structure."""
        found = False
        for root, dirs, files in os.walk(self.REPO_DIR):
            for f in files:
                if f.endswith(".zig"):
                    path = os.path.join(root, f)
                    with open(path, "r", errors="ignore") as fh:
                        content = fh.read()
                    if re.search(r"Class|JSClass|shim\.Class|defineClass|extern struct", content):
                        if re.search(r"URLPattern|url_pattern", content, re.IGNORECASE):
                            found = True
                            break
            if found:
                break
        assert found, "No JSC class definition for URLPattern in Zig"

    def test_constructor_function(self):
        """URLPattern must have a constructor function."""
        found = False
        for root, dirs, files in os.walk(self.REPO_DIR):
            for f in files:
                if f.endswith(".zig"):
                    path = os.path.join(root, f)
                    with open(path, "r", errors="ignore") as fh:
                        content = fh.read()
                    if re.search(r"URLPattern", content):
                        if re.search(r"constructor|init|create|new", content, re.IGNORECASE):
                            found = True
                            break
            if found:
                break
        assert found, "URLPattern constructor not found"

    def test_exec_or_test_method(self):
        """URLPattern must have exec() or test() method."""
        found = False
        for root, dirs, files in os.walk(self.REPO_DIR):
            for f in files:
                if f.endswith((".zig", ".ts", ".d.ts")):
                    path = os.path.join(root, f)
                    with open(path, "r", errors="ignore") as fh:
                        content = fh.read()
                    if "URLPattern" in content:
                        if re.search(r"\.exec\b|\"exec\"|\.test\b|\"test\"", content):
                            found = True
                            break
            if found:
                break
        assert found, "URLPattern exec/test method not found"

    def test_pattern_component_fields(self):
        """URLPattern must have component fields (protocol, hostname, pathname, etc)."""
        found = False
        for root, dirs, files in os.walk(self.REPO_DIR):
            for f in files:
                if f.endswith((".zig", ".ts")):
                    path = os.path.join(root, f)
                    with open(path, "r", errors="ignore") as fh:
                        content = fh.read()
                    if "URLPattern" in content:
                        if re.search(r"protocol|hostname|pathname|search|hash|port", content):
                            found = True
                            break
            if found:
                break
        assert found, "URLPattern component fields not found"

    def test_memory_management(self):
        """Zig code should handle memory allocation/deallocation."""
        found = False
        for root, dirs, files in os.walk(self.REPO_DIR):
            for f in files:
                if f.endswith(".zig"):
                    path = os.path.join(root, f)
                    with open(path, "r", errors="ignore") as fh:
                        content = fh.read()
                    if "URLPattern" in content or "url_pattern" in content.lower():
                        if re.search(r"allocator|alloc|dealloc|free|destroy|deinit", content):
                            found = True
                            break
            if found:
                break
        assert found, "No memory management in URLPattern Zig code"

    def test_error_handling_in_zig(self):
        """Zig code must handle errors (!type or error union)."""
        found = False
        for root, dirs, files in os.walk(self.REPO_DIR):
            for f in files:
                if f.endswith(".zig"):
                    path = os.path.join(root, f)
                    with open(path, "r", errors="ignore") as fh:
                        content = fh.read()
                    if "URLPattern" in content or "url_pattern" in content.lower():
                        if re.search(r"catch|try|error\.|![\w]|orelse", content):
                            found = True
                            break
            if found:
                break
        assert found, "No error handling in URLPattern Zig code"

    def test_js_bindings_export(self):
        """Zig code should export functions for JS runtime binding."""
        found = False
        for root, dirs, files in os.walk(self.REPO_DIR):
            for f in files:
                if f.endswith(".zig"):
                    path = os.path.join(root, f)
                    with open(path, "r", errors="ignore") as fh:
                        content = fh.read()
                    if "URLPattern" in content or "url_pattern" in content.lower():
                        if re.search(r"export|callconv|extern|JSValue|toJS|fromJS", content):
                            found = True
                            break
            if found:
                break
        assert found, "No JS binding exports found"

    def test_test_file_exists(self):
        """Test file for URLPattern must exist."""
        found = False
        for root, dirs, files in os.walk(self.REPO_DIR):
            for f in files:
                if f.endswith((".test.ts", ".test.js", "_test.zig", ".spec.ts")):
                    path = os.path.join(root, f)
                    with open(path, "r", errors="ignore") as fh:
                        content = fh.read()
                    if "URLPattern" in content:
                        found = True
                        break
            if found:
                break
        assert found, "No test file for URLPattern"

    def test_url_pattern_matching_logic(self):
        """URLPattern must implement pattern matching logic."""
        found = False
        for root, dirs, files in os.walk(self.REPO_DIR):
            for f in files:
                if f.endswith(".zig"):
                    path = os.path.join(root, f)
                    with open(path, "r", errors="ignore") as fh:
                        content = fh.read()
                    if "URLPattern" in content or "url_pattern" in content.lower():
                        if re.search(r"match|parse|compile|pattern|regex|glob", content, re.IGNORECASE):
                            found = True
                            break
            if found:
                break
        assert found, "No pattern matching logic found"
