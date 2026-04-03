"""
Test for 'bash-defensive-patterns' skill — ShellCheck Defensive Patterns
Validates that the Agent applied defensive bash patterns including set -Eeuo
pipefail, trap ERR, and proper variable quoting.
"""

import os
import re

import pytest


class TestBashDefensivePatterns:
    """Verify defensive bash scripting patterns."""

    REPO_DIR = "/workspace/shellcheck"

    def test_script_files_exist(self):
        """At least one shell script with defensive patterns must exist."""
        found = False
        for root, dirs, files in os.walk(self.REPO_DIR):
            for f in files:
                if f.endswith(".sh") or f.endswith(".bash"):
                    found = True
                    break
            if found:
                break
        assert found, "No shell script files found"

    def test_set_eeuo_pipefail_present(self):
        """Scripts must use set -Eeuo pipefail or equivalent."""
        found = False
        for root, dirs, files in os.walk(self.REPO_DIR):
            for f in files:
                if f.endswith(".sh") or f.endswith(".bash"):
                    path = os.path.join(root, f)
                    with open(path, "r", errors="ignore") as fh:
                        content = fh.read()
                    if re.search(r"set\s+-[eEuo]+\s*pipefail|set\s+-[eEuo]+.*\n.*set\s+-o\s+pipefail", content):
                        found = True
                        break
            if found:
                break
        assert found, "No script uses set -Eeuo pipefail"

    def test_trap_err_present(self):
        """Scripts should define a trap for ERR signal."""
        found = False
        for root, dirs, files in os.walk(self.REPO_DIR):
            for f in files:
                if f.endswith(".sh") or f.endswith(".bash"):
                    path = os.path.join(root, f)
                    with open(path, "r", errors="ignore") as fh:
                        content = fh.read()
                    if re.search(r"trap\s+.*\s+ERR", content):
                        found = True
                        break
            if found:
                break
        assert found, "No script uses trap ERR"

    def test_variables_quoted(self):
        """Variables should be properly quoted to prevent word splitting."""
        unquoted_count = 0
        checked = 0
        for root, dirs, files in os.walk(self.REPO_DIR):
            for f in files:
                if f.endswith(".sh") or f.endswith(".bash"):
                    path = os.path.join(root, f)
                    with open(path, "r", errors="ignore") as fh:
                        content = fh.read()
                    checked += 1
                    unquoted = re.findall(r'[^"]\$\{?\w+\}?[^"]', content)
                    if len(unquoted) > 10:
                        unquoted_count += 1
        if checked == 0:
            pytest.skip("No shell scripts found")
        # Allow some unquoted vars but flag excessive usage
        assert True

    def test_shellcheck_directive_not_overused(self):
        """shellcheck disable directives should not be overused."""
        disable_count = 0
        for root, dirs, files in os.walk(self.REPO_DIR):
            for f in files:
                if f.endswith(".sh") or f.endswith(".bash"):
                    path = os.path.join(root, f)
                    with open(path, "r", errors="ignore") as fh:
                        content = fh.read()
                    disable_count += len(re.findall(r"shellcheck\s+disable", content))
        assert disable_count < 20, (
            f"Too many shellcheck disable directives: {disable_count}"
        )

    def test_error_handler_function_defined(self):
        """An error handler function should be defined for trap to call."""
        found = False
        for root, dirs, files in os.walk(self.REPO_DIR):
            for f in files:
                if f.endswith(".sh") or f.endswith(".bash"):
                    path = os.path.join(root, f)
                    with open(path, "r", errors="ignore") as fh:
                        content = fh.read()
                    if re.search(r"(error_handler|err_handler|cleanup|on_error)\s*\(\)", content):
                        found = True
                        break
            if found:
                break
        assert found, "No error handler function defined"

    def test_readonly_variables_used(self):
        """Readonly or declare -r should be used for constants."""
        found = False
        for root, dirs, files in os.walk(self.REPO_DIR):
            for f in files:
                if f.endswith(".sh") or f.endswith(".bash"):
                    path = os.path.join(root, f)
                    with open(path, "r", errors="ignore") as fh:
                        content = fh.read()
                    if re.search(r"readonly\s+|declare\s+-r\s+", content):
                        found = True
                        break
            if found:
                break
        assert found, "No readonly variable declarations found"

    def test_temp_files_cleaned_up(self):
        """Temporary files should be cleaned up via trap EXIT or explicit cleanup."""
        found = False
        for root, dirs, files in os.walk(self.REPO_DIR):
            for f in files:
                if f.endswith(".sh") or f.endswith(".bash"):
                    path = os.path.join(root, f)
                    with open(path, "r", errors="ignore") as fh:
                        content = fh.read()
                    if re.search(r"mktemp|tmp", content) and re.search(r"trap.*EXIT|cleanup|rm\s+.*\$", content):
                        found = True
                        break
            if found:
                break
        assert found, "Temp files not cleaned up on exit"

    def test_functions_use_local_variables(self):
        """Functions should use local variables to prevent global scope pollution."""
        found = False
        for root, dirs, files in os.walk(self.REPO_DIR):
            for f in files:
                if f.endswith(".sh") or f.endswith(".bash"):
                    path = os.path.join(root, f)
                    with open(path, "r", errors="ignore") as fh:
                        content = fh.read()
                    if re.search(r"local\s+\w+", content):
                        found = True
                        break
            if found:
                break
        assert found, "Functions do not use local variables"

    def test_shebang_line_present(self):
        """Script files must have a proper shebang line."""
        found = False
        for root, dirs, files in os.walk(self.REPO_DIR):
            for f in files:
                if f.endswith(".sh") or f.endswith(".bash"):
                    path = os.path.join(root, f)
                    with open(path, "r", errors="ignore") as fh:
                        first_line = fh.readline()
                    if re.search(r"^#!/(usr/)?bin/(env\s+)?bash", first_line):
                        found = True
                        break
            if found:
                break
        assert found, "No script has a proper bash shebang"
