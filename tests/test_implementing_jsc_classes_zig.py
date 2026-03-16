"""
Test for 'implementing-jsc-classes-zig' skill — JSC Classes in Zig (Bun)
Validates that the Agent implemented JavaScript Core (JSC) class bindings
in Zig within the Bun runtime.
"""

import os
import subprocess
import pytest


class TestImplementingJscClassesZig:
    """Verify JSC class implementation in Zig for Bun."""

    REPO_DIR = "/workspace/bun"

    # ------------------------------------------------------------------
    # L1: file existence
    # ------------------------------------------------------------------

    def test_zig_source_exists(self):
        """New Zig JSC class file must exist."""
        found = []
        for root, dirs, files in os.walk(self.REPO_DIR):
            for f in files:
                if f.endswith(".zig") and "node_modules" not in root:
                    fpath = os.path.join(root, f)
                    try:
                        with open(fpath, "r", errors="ignore") as fh:
                            content = fh.read()
                        if (
                            "JSC" in content
                            or "JSValue" in content
                            or "JSGlobalObject" in content
                        ):
                            found.append(fpath)
                    except OSError:
                        pass
        assert len(found) >= 1, "No Zig JSC class file found"

    def test_test_file_exists(self):
        """Test file for JSC class must exist."""
        found = []
        patterns = ["test", "spec"]
        for root, dirs, files in os.walk(self.REPO_DIR):
            for f in files:
                if (
                    any(p in f.lower() for p in patterns)
                    and (f.endswith((".zig", ".js", ".ts")))
                    and "node_modules" not in root
                ):
                    found.append(os.path.join(root, f))
        assert len(found) >= 1, "No test file found"

    # ------------------------------------------------------------------
    # L2: content validation
    # ------------------------------------------------------------------

    def _find_jsc_zig_files(self):
        found = []
        for root, dirs, files in os.walk(self.REPO_DIR):
            for f in files:
                if f.endswith(".zig") and "node_modules" not in root:
                    fpath = os.path.join(root, f)
                    try:
                        with open(fpath, "r", errors="ignore") as fh:
                            content = fh.read()
                        if "JSC" in content or "JSValue" in content:
                            found.append(fpath)
                    except OSError:
                        pass
        return found

    def _read_all_jsc(self):
        content = ""
        for fpath in self._find_jsc_zig_files():
            with open(fpath, "r", errors="ignore") as f:
                content += f.read() + "\n"
        return content

    def test_struct_definition(self):
        """Must define a Zig struct for the JSC class."""
        content = self._read_all_jsc()
        assert "struct" in content, "No struct definition found"

    def test_jsc_class_interface(self):
        """Must implement JSC class interface methods."""
        content = self._read_all_jsc()
        interface_patterns = [
            "getProperty",
            "setProperty",
            "constructor",
            "finalize",
            "call",
            "JSClassDefinition",
            "toJS",
            "fromJS",
            "getter",
            "setter",
        ]
        found = sum(1 for p in interface_patterns if p in content)
        assert found >= 3, f"Only {found} JSC interface methods found"

    def test_memory_management(self):
        """Must handle memory management (allocator)."""
        content = self._read_all_jsc()
        mem_patterns = [
            "allocator",
            "alloc",
            "free",
            "destroy",
            "deinit",
            "Allocator",
            "GC",
            "ref_count",
        ]
        found = any(p in content for p in mem_patterns)
        assert found, "No memory management found"

    def test_error_handling(self):
        """Must implement error handling."""
        content = self._read_all_jsc()
        error_patterns = [
            "error",
            "catch",
            "throw",
            "JSError",
            "makeError",
            "createError",
            "try",
        ]
        found = any(p in content.lower() for p in error_patterns)
        assert found, "No error handling found"

    def test_js_value_conversions(self):
        """Must convert between JS values and Zig types."""
        content = self._read_all_jsc()
        conv_patterns = [
            "toJSValue",
            "fromJS",
            "toString",
            "toNumber",
            "JSStringRef",
            "JSValueRef",
            "jsNumber",
            "jsString",
            "toZigString",
        ]
        found = sum(1 for p in conv_patterns if p in content)
        assert found >= 2, "Insufficient JS value conversions"

    def test_export_to_js(self):
        """Class must be exported/registered for JS use."""
        content = self._read_all_jsc()
        export_patterns = [
            "export",
            "register",
            "JSClassCreate",
            "defineProperty",
            "globalObject",
            "comptime",
            "pub fn",
        ]
        found = sum(1 for p in export_patterns if p in content)
        assert found >= 2, "Class not properly exported for JS use"

    def test_zig_build_check(self):
        """Zig files must have valid syntax (basic check)."""
        for fpath in self._find_jsc_zig_files():
            with open(fpath, "r") as f:
                content = f.read()
            # Basic bracket balance
            opens = content.count("{")
            closes = content.count("}")
            diff = abs(opens - closes)
            assert diff <= 2, f"{fpath} has bracket imbalance: {diff}"

    def test_at_least_3_methods(self):
        """JSC class must expose at least 3 methods."""
        content = self._read_all_jsc()
        import re

        pub_fns = re.findall(r"pub\s+fn\s+(\w+)", content)
        assert len(pub_fns) >= 3, f"Only {len(pub_fns)} pub fn definitions found"
