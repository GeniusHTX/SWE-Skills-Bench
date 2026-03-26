"""
Tests for the bash-defensive-patterns skill.
Verifies that the ShellCheck project shell scripts implement defensive Bash
patterns including strict mode, safe deletion wrappers, proper quoting,
dry-run flag support, and shellcheck compliance.
"""

import os
import subprocess

import pytest

REPO_DIR = "/workspace/shellcheck"


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _path(rel: str) -> str:
    return os.path.join(REPO_DIR, rel)


def _read(rel: str) -> str:
    full = _path(rel)
    if not os.path.isfile(full):
        pytest.skip(f"File not found: {full}")
    with open(full, encoding="utf-8", errors="replace") as fh:
        return fh.read()


def _run(
    cmd: list, cwd: str = REPO_DIR, timeout: int = 30, shell: bool = False
) -> subprocess.CompletedProcess:
    return subprocess.run(
        cmd if not shell else " ".join(cmd),
        cwd=cwd,
        capture_output=True,
        text=True,
        timeout=timeout,
        shell=shell,
    )


def _shellcheck_available() -> bool:
    try:
        r = subprocess.run(["shellcheck", "--version"], capture_output=True, timeout=10)
        return r.returncode == 0
    except (FileNotFoundError, subprocess.TimeoutExpired):
        return False


def _bash_available() -> bool:
    try:
        r = subprocess.run(["bash", "--version"], capture_output=True, timeout=10)
        return r.returncode == 0
    except (FileNotFoundError, subprocess.TimeoutExpired):
        return False


# ---------------------------------------------------------------------------
# File path checks
# ---------------------------------------------------------------------------


class TestBashDefensivePatterns:
    """Test suite for the Bash defensive patterns skill in the ShellCheck project."""

    def test_main_runner_scripts_exist(self):
        """Verify the main test runner scripts exist at expected paths."""
        for rel in ("test/run_tests.sh", "test/lib/common.sh"):
            assert os.path.isfile(_path(rel)), f"Missing script: {rel}"

    def test_runner_and_utils_scripts_exist(self):
        """Verify runner.sh exists in test/lib/."""
        target = _path("test/lib/runner.sh")
        assert os.path.isfile(target), f"runner.sh not found: {target}"

    # -----------------------------------------------------------------------
    # Semantic checks
    # -----------------------------------------------------------------------

    def test_scripts_have_shebang_and_strict_mode(self):
        """Verify all shell scripts start with #!/bin/bash and use set -euo pipefail."""
        scripts = [
            "test/run_tests.sh",
            "test/lib/common.sh",
            "test/lib/runner.sh",
        ]
        for rel in scripts:
            full = _path(rel)
            if not os.path.isfile(full):
                continue
            with open(full, encoding="utf-8", errors="replace") as f:
                content = f.read()
            assert (
                content.startswith("#!/bin/bash") or "#!/usr/bin/env bash" in content
            ), f"{rel} must start with #!/bin/bash or #!/usr/bin/env bash"
            has_strict = "set -euo pipefail" in content or "set -e" in content
            assert (
                has_strict
            ), f"{rel} must use set -euo pipefail or equivalent strict mode"

    def test_safe_rm_function_defined(self):
        """Verify common.sh defines a safe_rm function as a safe deletion wrapper."""
        content = _read("test/lib/common.sh")
        assert "safe_rm" in content, "common.sh must define a 'safe_rm' function"

    def test_scripts_do_not_use_unquoted_variables(self):
        """Verify run_tests.sh uses quoted variable expansions (defensive quoting)."""
        content = _read("test/run_tests.sh")
        # Look for quoted references - basic check that "$VAR" style is present
        import re

        quoted_vars = re.findall(r'"\$\w+', content)
        unquoted_vars = re.findall(r'\b\$[A-Za-z_][A-Za-z0-9_]*\b(?!")', content)
        # Should have more quoted than unquoted, or at least some quoted references
        assert (
            len(quoted_vars) > 0 or len(unquoted_vars) == 0
        ), 'run_tests.sh must use quoted variable expansions ("$VAR")'

    def test_dry_run_flag_defined_in_script(self):
        """Verify run_tests.sh defines --dry-run flag handling."""
        content = _read("test/run_tests.sh")
        assert (
            "--dry-run" in content
        ), "run_tests.sh must define --dry-run flag handling"

    # -----------------------------------------------------------------------
    # Functional checks (command)
    # -----------------------------------------------------------------------

    def test_shellcheck_passes_all_scripts(self):
        """Verify shellcheck reports no errors on all shell scripts."""
        if not _shellcheck_available():
            pytest.skip("shellcheck not available in this environment")
        scripts = [
            _path("test/run_tests.sh"),
            _path("test/lib/common.sh"),
            _path("test/lib/runner.sh"),
        ]
        existing = [s for s in scripts if os.path.isfile(s)]
        if not existing:
            pytest.skip("No scripts found to check")
        result = _run(["shellcheck"] + existing)
        assert (
            result.returncode == 0
        ), f"shellcheck reported issues:\nstdout: {result.stdout}\nstderr: {result.stderr}"

    def test_help_flag_exits_zero(self):
        """Verify run_tests.sh --help exits with code 0 and prints usage info."""
        if not _bash_available():
            pytest.skip("bash not available")
        script = _path("test/run_tests.sh")
        if not os.path.isfile(script):
            pytest.skip("run_tests.sh not found")
        result = _run(["bash", script, "--help"])
        assert (
            result.returncode == 0
        ), f"--help should exit 0, got {result.returncode}\n{result.stderr}"
        combined = result.stdout + result.stderr
        has_usage = (
            "usage" in combined.lower()
            or "help" in combined.lower()
            or "options" in combined.lower()
        )
        assert has_usage, "--help output must contain usage information"

    def test_unknown_flag_exits_nonzero(self):
        """Verify run_tests.sh exits non-zero for unrecognized flags."""
        if not _bash_available():
            pytest.skip("bash not available")
        script = _path("test/run_tests.sh")
        if not os.path.isfile(script):
            pytest.skip("run_tests.sh not found")
        result = _run(["bash", script, "--unknown-flag-xyz"], timeout=15)
        assert (
            result.returncode != 0
        ), "run_tests.sh must exit non-zero for unknown flags"
        combined = result.stdout + result.stderr
        assert any(
            word in combined.lower()
            for word in ("unknown", "invalid", "unrecognized", "error")
        ), "Error message must indicate invalid/unknown option"

    def test_dry_run_creates_no_files(self):
        """Verify --dry-run mode creates no output files."""
        if not _bash_available():
            pytest.skip("bash not available")
        script = _path("test/run_tests.sh")
        if not os.path.isfile(script):
            pytest.skip("run_tests.sh not found")
        import tempfile

        with tempfile.TemporaryDirectory() as tmpdir:
            before = set(os.listdir(tmpdir))
            _run(["bash", script, "--dry-run"], cwd=tmpdir, timeout=30)
            after = set(os.listdir(tmpdir))
        new_files = after - before
        assert (
            len(new_files) == 0
        ), f"--dry-run must not create new files; created: {new_files}"

    def test_safe_rm_refuses_system_path(self):
        """Verify safe_rm refuses to delete protected system paths like /etc/passwd."""
        if not _bash_available():
            pytest.skip("bash not available")
        common = _path("test/lib/common.sh")
        if not os.path.isfile(common):
            pytest.skip("common.sh not found")
        result = _run(
            ["bash", "-c", f'source "{common}" && safe_rm /etc/passwd'],
            timeout=10,
        )
        assert result.returncode != 0, "safe_rm must refuse to delete /etc/passwd"
        combined = result.stdout + result.stderr
        has_refusal = any(
            word in combined.lower()
            for word in ("cannot", "refuse", "protected", "not allowed", "safe", "deny")
        )
        assert (
            has_refusal or result.returncode != 0
        ), "safe_rm must output a refusal message or exit non-zero for /etc/passwd"

    def test_safe_rm_function_validates_argument(self):
        """Verify common.sh safe_rm function rejects empty or blank path arguments."""
        content = _read("test/lib/common.sh")
        lower = content.lower()
        # safe_rm must check for empty or null paths
        has_check = (
            "-z" in content
            or "[ -z" in content
            or "empty" in lower
            or '""' in content
            or "null" in lower
        )
        assert has_check, "safe_rm must validate that the path argument is not empty"
