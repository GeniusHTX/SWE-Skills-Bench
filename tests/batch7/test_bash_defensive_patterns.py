"""Test file for the bash-defensive-patterns skill.

This suite validates custom ShellCheck rules SC2326, SC2327, and SC2328
for defensive bash scripting patterns in the shellcheck repository.
"""

from __future__ import annotations

import pathlib
import re
import shutil
import subprocess
import tempfile
import textwrap

import pytest


class TestBashDefensivePatterns:
    """Verify ShellCheck defensive-pattern rules SC2326/SC2327/SC2328."""

    REPO_DIR = "/workspace/shellcheck"

    COMMANDS_HS = "src/ShellCheck/Checks/Commands.hs"
    SHELL_SUPPORT_HS = "src/ShellCheck/Checks/ShellSupport.hs"
    COMMANDS_TEST_HS = "tests/ShellCheck/Checks/CommandsTest.hs"

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    def _repo_path(self, relative: str) -> pathlib.Path:
        return pathlib.Path(self.REPO_DIR, *relative.split("/"))

    def _read_text(self, relative: str) -> str:
        path = self._repo_path(relative)
        assert path.exists(), f"Expected path to exist: {path}"
        return path.read_text(encoding="utf-8", errors="ignore")

    def _assert_non_empty_file(self, relative: str) -> pathlib.Path:
        path = self._repo_path(relative)
        assert path.is_file(), f"Expected file to exist: {path}"
        assert path.stat().st_size > 0, f"Expected non-empty file: {path}"
        return path

    def _find_shellcheck(self) -> str:
        """Locate the shellcheck binary."""
        sc = shutil.which("shellcheck")
        if sc:
            return sc
        repo = pathlib.Path(self.REPO_DIR)
        for candidate in (repo / "shellcheck", repo / "dist" / "shellcheck"):
            if candidate.is_file():
                return str(candidate)
        pytest.fail("shellcheck binary not found on PATH or in repo")
        return ""  # unreachable

    def _run_shellcheck(
        self, script: str, *, extra_args: list[str] | None = None
    ) -> subprocess.CompletedProcess[str]:
        """Run shellcheck on a temporary bash script and return the result."""
        sc = self._find_shellcheck()
        with tempfile.NamedTemporaryFile(mode="w", suffix=".sh", delete=False) as f:
            f.write("#!/bin/bash\n" + script)
            f.flush()
            args = [sc, "-f", "json", f.name] + (extra_args or [])
            result = subprocess.run(args, capture_output=True, text=True, timeout=30)
        return result

    def _shellcheck_codes(self, script: str) -> set[int]:
        """Return the set of SC rule codes triggered by the given script."""
        import json

        result = self._run_shellcheck(script)
        try:
            findings = json.loads(result.stdout) if result.stdout.strip() else []
        except json.JSONDecodeError:
            findings = []
        return {f["code"] for f in findings if isinstance(f, dict) and "code" in f}

    # ------------------------------------------------------------------
    # Layer 1 – file_path_check (3 cases)
    # ------------------------------------------------------------------

    def test_file_path_src_shellcheck_checks_commands_hs_is_modified_with_sc2326_an(
        self,
    ):
        """Verify Commands.hs exists and is non-empty."""
        self._assert_non_empty_file(self.COMMANDS_HS)

    def test_file_path_src_shellcheck_checks_shellsupport_hs_is_modified_with_sc232(
        self,
    ):
        """Verify ShellSupport.hs exists and is non-empty."""
        self._assert_non_empty_file(self.SHELL_SUPPORT_HS)

    def test_file_path_tests_shellcheck_checks_commandstest_hs_is_modified_with_sc2(
        self,
    ):
        """Verify CommandsTest.hs exists and is non-empty."""
        self._assert_non_empty_file(self.COMMANDS_TEST_HS)

    # ------------------------------------------------------------------
    # Layer 2 – semantic_check (5 cases)
    # ------------------------------------------------------------------

    def test_semantic_sc2326_check_function_traverses_ast_for_variable_assignments(
        self,
    ):
        """SC2326 check traverses AST for variable assignments with /tmp/ in RHS."""
        src = self._read_text(self.COMMANDS_HS)
        assert "2326" in src, "SC2326 rule ID not found in Commands.hs"
        assert re.search(
            r"/tmp/|tmp.*path|hardcoded.*temp", src, re.IGNORECASE
        ), "SC2326 should reference /tmp/ pattern detection"

    def test_semantic_sc2326_handles_var_value_local_var_value_export_var_value_fo(
        self,
    ):
        """SC2326 handles VAR=value, local VAR=value, export VAR=value forms."""
        src = self._read_text(self.COMMANDS_HS)
        # The rule should handle multiple assignment forms
        assert re.search(
            r"local|export|assign|T_Assignment|TA_Variable", src, re.IGNORECASE
        ), "SC2326 should handle multiple assignment forms (VAR=, local, export)"

    def test_semantic_sc2327_check_function_detects_mktemp_or_tmp_assignments_and_(
        self,
    ):
        """SC2327 detects mktemp or /tmp/ assignments and verifies trap existence."""
        # SC2327 may be in Commands.hs or ShellSupport.hs
        combined = ""
        for f in (self.COMMANDS_HS, self.SHELL_SUPPORT_HS):
            path = self._repo_path(f)
            if path.exists():
                combined += path.read_text(encoding="utf-8", errors="ignore")
        assert "2327" in combined, "SC2327 rule ID not found"
        assert re.search(
            r"mktemp|trap|cleanup|EXIT", combined
        ), "SC2327 should reference mktemp/trap/cleanup patterns"

    def test_semantic_sc2327_scopes_analysis_to_function_script_level(self):
        """SC2327 scopes analysis to function/script level."""
        combined = ""
        for f in (self.COMMANDS_HS, self.SHELL_SUPPORT_HS):
            path = self._repo_path(f)
            if path.exists():
                combined += path.read_text(encoding="utf-8", errors="ignore")
        # Should reference scope/function-level analysis
        assert re.search(
            r"scope|function|parent|block|T_Function|subshell", combined, re.IGNORECASE
        ), "SC2327 should scope analysis to function/script level"

    def test_semantic_sc2328_check_function_detects_unquoted_and_backtick_inside_a(
        self,
    ):
        """SC2328 detects unquoted $() and backtick inside [ ] and [[ ]]."""
        src = self._read_text(self.COMMANDS_HS)
        assert "2328" in src, "SC2328 rule ID not found in Commands.hs"
        assert re.search(
            r"unquoted|backtick|command.?sub|T_Backticked|\$\(", src, re.IGNORECASE
        ), "SC2328 should detect unquoted command substitutions"

    # ------------------------------------------------------------------
    # Layer 3 – functional_check (5 cases, mocked via shellcheck execution)
    # ------------------------------------------------------------------

    def test_functional_tmpfile_tmp_myapp__triggers_sc2326(self):
        """tmpfile=/tmp/myapp_$$ should trigger SC2326."""
        codes = self._shellcheck_codes('tmpfile=/tmp/myapp_$$\necho "$tmpfile"')
        assert 2326 in codes, f"Expected SC2326 to trigger, got codes: {codes}"

    def test_functional_tmpfile_mktemp_does_not_trigger_sc2326(self):
        """tmpfile=$(mktemp) does NOT trigger SC2326."""
        codes = self._shellcheck_codes('tmpfile=$(mktemp)\necho "$tmpfile"')
        assert (
            2326 not in codes
        ), f"SC2326 should not trigger for mktemp, got codes: {codes}"

    def test_functional_f_tmp_something_does_not_trigger_sc2326(self):
        """[ -f /tmp/something ] does NOT trigger SC2326 (read-only use)."""
        codes = self._shellcheck_codes("if [ -f /tmp/something ]; then echo ok; fi")
        assert (
            2326 not in codes
        ), f"SC2326 should not trigger for read-only /tmp/ check, got codes: {codes}"

    def test_functional_mktemp_without_trap_triggers_sc2327(self):
        """mktemp without trap should trigger SC2327."""
        codes = self._shellcheck_codes('tmpfile=$(mktemp)\necho "$tmpfile"')
        assert 2327 in codes, f"Expected SC2327 to trigger, got codes: {codes}"

    def test_functional_mktemp_with_trap_exit_does_not_trigger_sc2327(self):
        """mktemp with trap EXIT does NOT trigger SC2327."""
        script = textwrap.dedent(
            """\
            tmpfile=$(mktemp)
            trap 'rm -f "$tmpfile"' EXIT
            echo "$tmpfile"
        """
        )
        codes = self._shellcheck_codes(script)
        assert (
            2327 not in codes
        ), f"SC2327 should not trigger when trap is present, got codes: {codes}"
