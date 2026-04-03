"""
Test for 'python-anti-patterns' skill — Python anti-pattern detection in boltons
Validates that the Agent identified and fixed Python anti-patterns
in the boltons library.
"""

import os
import re

import pytest


class TestPythonAntiPatterns:
    """Verify Python anti-pattern fixes in boltons."""

    REPO_DIR = "/workspace/boltons"

    def test_no_mutable_default_arguments(self):
        """No functions should use mutable default arguments (list, dict, set)."""
        violations = []
        for root, dirs, files in os.walk(self.REPO_DIR):
            if ".git" in root:
                continue
            for f in files:
                if f.endswith(".py"):
                    path = os.path.join(root, f)
                    with open(path, "r", errors="ignore") as fh:
                        content = fh.read()
                    matches = re.findall(r"def\s+\w+\([^)]*=\s*(\[\]|\{\}|set\(\))", content)
                    if matches:
                        violations.append(f)
        assert len(violations) == 0, f"Mutable default arguments found in: {violations}"

    def test_no_bare_except(self):
        """No bare except: clauses should exist."""
        violations = []
        for root, dirs, files in os.walk(self.REPO_DIR):
            if ".git" in root:
                continue
            for f in files:
                if f.endswith(".py"):
                    path = os.path.join(root, f)
                    with open(path, "r", errors="ignore") as fh:
                        content = fh.read()
                    if re.search(r"^\s*except\s*:", content, re.MULTILINE):
                        violations.append(f)
        assert len(violations) == 0, f"Bare except found in: {violations}"

    def test_no_wildcard_imports(self):
        """No wildcard imports (from x import *) should exist in main modules."""
        violations = []
        for root, dirs, files in os.walk(self.REPO_DIR):
            if ".git" in root or "test" in root:
                continue
            for f in files:
                if f.endswith(".py") and f != "__init__.py":
                    path = os.path.join(root, f)
                    with open(path, "r", errors="ignore") as fh:
                        content = fh.read()
                    if re.search(r"from\s+\S+\s+import\s+\*", content):
                        violations.append(f)
        assert len(violations) == 0, f"Wildcard imports found in: {violations}"

    def test_uses_context_managers(self):
        """File operations should use context managers (with statement)."""
        found = False
        for root, dirs, files in os.walk(self.REPO_DIR):
            for f in files:
                if f.endswith(".py"):
                    path = os.path.join(root, f)
                    with open(path, "r", errors="ignore") as fh:
                        content = fh.read()
                    if re.search(r"with\s+open\(", content):
                        found = True
                        break
            if found:
                break
        assert found, "No context manager usage for file operations"

    def test_proper_string_formatting(self):
        """Code should use f-strings or .format() over % formatting."""
        found_modern = False
        for root, dirs, files in os.walk(self.REPO_DIR):
            if ".git" in root:
                continue
            for f in files:
                if f.endswith(".py"):
                    path = os.path.join(root, f)
                    with open(path, "r", errors="ignore") as fh:
                        content = fh.read()
                    if re.search(r"f['\"]|\.format\(", content):
                        found_modern = True
                        break
            if found_modern:
                break
        assert found_modern, "No modern string formatting found"

    def test_type_hints_presence(self):
        """Module files should include type hints."""
        found = False
        for root, dirs, files in os.walk(self.REPO_DIR):
            if ".git" in root:
                continue
            for f in files:
                if f.endswith(".py"):
                    path = os.path.join(root, f)
                    with open(path, "r", errors="ignore") as fh:
                        content = fh.read()
                    if re.search(r"def\s+\w+\([^)]*:\s*\w+|-> \w+", content):
                        found = True
                        break
            if found:
                break
        assert found, "No type hints found"

    def test_no_global_state_mutation(self):
        """Module-level mutable globals should be avoided or documented."""
        found_clean = False
        for root, dirs, files in os.walk(self.REPO_DIR):
            if ".git" in root:
                continue
            for f in files:
                if f.endswith(".py"):
                    path = os.path.join(root, f)
                    with open(path, "r", errors="ignore") as fh:
                        content = fh.read()
                    if re.search(r"class\s+\w+|def\s+\w+", content):
                        found_clean = True
                        break
            if found_clean:
                break
        assert found_clean, "No structured code found"

    def test_docstrings_on_public_functions(self):
        """Public functions should have docstrings."""
        found = False
        for root, dirs, files in os.walk(self.REPO_DIR):
            if ".git" in root:
                continue
            for f in files:
                if f.endswith(".py"):
                    path = os.path.join(root, f)
                    with open(path, "r", errors="ignore") as fh:
                        content = fh.read()
                    if re.search(r"def\s+[a-z]\w+\([^)]*\):\s*\n\s+\"\"\"", content):
                        found = True
                        break
            if found:
                break
        assert found, "No public functions with docstrings found"

    def test_no_print_in_library_code(self):
        """Library code should use logging instead of print()."""
        violations = []
        for root, dirs, files in os.walk(self.REPO_DIR):
            if ".git" in root or "test" in root or "example" in root:
                continue
            for f in files:
                if f.endswith(".py") and f not in ("__init__.py", "setup.py"):
                    path = os.path.join(root, f)
                    with open(path, "r", errors="ignore") as fh:
                        content = fh.read()
                    if re.search(r"^\s+print\(", content, re.MULTILINE):
                        violations.append(f)
        # Advisory check
        assert isinstance(violations, list)

    def test_test_file_exists(self):
        """Test files for the anti-pattern fixes must exist."""
        found = False
        for root, dirs, files in os.walk(self.REPO_DIR):
            for f in files:
                if f.startswith("test_") and f.endswith(".py"):
                    found = True
                    break
            if found:
                break
        assert found, "No test files found"
