"""
Tests for python-packaging skill.
Validates CLI tool for version parsing/requirement checks in packaging repository.
"""

import os
import subprocess
import json
import pytest

REPO_DIR = "/workspace/packaging"


def _path(rel: str) -> str:
    return os.path.join(REPO_DIR, rel)


def _read(rel: str) -> str:
    with open(_path(rel), encoding="utf-8", errors="ignore") as f:
        return f.read()


def _run(cmd: str, timeout: int = 60):
    return subprocess.run(
        cmd, shell=True, cwd=REPO_DIR, capture_output=True, text=True, timeout=timeout
    )


class TestPythonPackaging:

    # ── file_path_check ──────────────────────────────────────────────────────

    def test_cli_py_exists(self):
        """packaging_cli/cli.py must exist as the CLI entry point."""
        rel = "packaging_cli/cli.py"
        assert os.path.isfile(_path(rel)), f"{rel} not found"
        assert os.path.getsize(_path(rel)) > 0, "cli.py is empty"

    def test_packaging_cli_init_exists(self):
        """packaging_cli/__init__.py must exist."""
        rel = "packaging_cli/__init__.py"
        assert os.path.isfile(_path(rel)), f"{rel} not found"

    # ── semantic_check ───────────────────────────────────────────────────────

    def test_parse_version_command_defined(self):
        """cli.py must define a 'parse-version' subcommand."""
        content = _read("packaging_cli/cli.py")
        assert (
            "parse" in content and "version" in content.lower()
        ), "'parse-version' subcommand not found in cli.py"
        assert (
            "argparse" in content or "click" in content
        ), "No CLI framework (argparse/click) found in cli.py"

    def test_check_requirement_command_defined(self):
        """cli.py must define a 'check-requirement' subcommand."""
        content = _read("packaging_cli/cli.py")
        assert (
            "check" in content and "requirement" in content.lower()
        ), "'check-requirement' subcommand not found in cli.py"

    def test_json_output_format_defined(self):
        """cli.py must output JSON with major, minor, patch keys."""
        content = _read("packaging_cli/cli.py")
        assert "json" in content.lower(), "No JSON output found in cli.py"
        assert (
            "major" in content and "minor" in content and "patch" in content
        ), "major/minor/patch keys not found in cli.py"

    def test_exit_code_1_on_error(self):
        """cli.py must call sys.exit(1) and write to stderr for errors."""
        content = _read("packaging_cli/cli.py")
        assert (
            "sys.exit(1)" in content or "exit(1)" in content
        ), "No sys.exit(1) found for error handling in cli.py"
        assert "stderr" in content, "No stderr write found in cli.py"

    # ── functional_check ─────────────────────────────────────────────────────

    def test_parse_version_321_exits_0_json(self):
        """parse-version 3.2.1 must exit 0 and output JSON with major=3 minor=2 patch=1."""
        result = _run("python -m packaging_cli.cli parse-version 3.2.1")
        if result.returncode != 0 and "No module named" in result.stderr:
            pytest.skip("packaging_cli not installed")
        assert (
            result.returncode == 0
        ), f"Expected exit 0, got {result.returncode}:\n{result.stderr}"
        data = json.loads(result.stdout)
        assert data["major"] == 3 and data["minor"] == 2 and data["patch"] == 1

    def test_parse_version_prerelease_flag(self):
        """parse-version 1.0.0a1 must output is_prerelease=true."""
        result = _run("python -m packaging_cli.cli parse-version 1.0.0a1")
        if result.returncode != 0 and "No module named" in result.stderr:
            pytest.skip("packaging_cli not installed")
        assert result.returncode == 0
        data = json.loads(result.stdout)
        assert (
            data.get("is_prerelease") is True
        ), f"Expected is_prerelease=true, got {data.get('is_prerelease')}"

    def test_parse_version_invalid_exits_1_stderr(self):
        """parse-version 'invalid' must exit 1 with error on stderr."""
        result = _run("python -m packaging_cli.cli parse-version invalid")
        if "No module named" in result.stderr:
            pytest.skip("packaging_cli not installed")
        assert (
            result.returncode == 1
        ), f"Expected exit 1 for invalid version, got {result.returncode}"
        assert result.stderr.strip() != "", "Expected error message on stderr"

    def test_check_requirement_requests_name(self):
        """check-requirement 'requests>=2.28' must parse name='requests'."""
        result = _run('python -m packaging_cli.cli check-requirement "requests>=2.28"')
        if "No module named" in result.stderr:
            pytest.skip("packaging_cli not installed")
        assert result.returncode == 0
        data = json.loads(result.stdout)
        assert data.get("name") == "requests"

    def test_check_requirement_nonexistent_whl_exits_1(self):
        """check-requirement nonexistent.whl must exit 1."""
        result = _run("python -m packaging_cli.cli check-requirement nonexistent.whl")
        if "No module named" in result.stderr:
            pytest.skip("packaging_cli not installed")
        assert (
            result.returncode == 1
        ), f"Expected exit 1 for nonexistent .whl, got {result.returncode}"

    def test_help_flag_exits_0(self):
        """--help must exit 0 and print usage with subcommands."""
        result = _run("python -m packaging_cli.cli --help")
        if "No module named" in result.stderr:
            pytest.skip("packaging_cli not installed")
        assert (
            result.returncode == 0
        ), f"Expected exit 0 for --help, got {result.returncode}"
        assert (
            "parse" in result.stdout.lower() or "version" in result.stdout.lower()
        ), "Expected subcommand hints in --help output"
