"""
Tests for the bazel-build-optimization skill.
Verifies that the Bazel build configuration for the Python Bazel example
correctly defines WORKSPACE with rules_python/pip, BUILD with py_binary/library/test
targets, a .bazelrc with required optimization flags, and a custom codegen.bzl rule.
"""

import os
import re

import pytest

REPO_DIR = "/workspace/bazel"


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


# ---------------------------------------------------------------------------
# File path checks
# ---------------------------------------------------------------------------


class TestBazelBuildOptimization:
    """Test suite for the Bazel build optimization skill."""

    def test_workspace_file_exists(self):
        """Verify WORKSPACE file exists and is non-empty."""
        target = _path("examples/python-bazel/WORKSPACE")
        assert os.path.isfile(target), f"WORKSPACE not found: {target}"
        assert os.path.getsize(target) > 0, "WORKSPACE must be non-empty"

    def test_bazelrc_and_bzl_files_exist(self):
        """Verify .bazelrc and codegen.bzl files exist."""
        for rel in (
            "examples/python-bazel/.bazelrc",
            "examples/python-bazel/rules/codegen.bzl",
        ):
            assert os.path.isfile(_path(rel)), f"Missing file: {rel}"

    def test_build_file_exists(self):
        """Verify BUILD file exists in the python-bazel example."""
        target = _path("examples/python-bazel/BUILD")
        assert os.path.isfile(target), f"BUILD not found: {target}"

    # -----------------------------------------------------------------------
    # Semantic checks
    # -----------------------------------------------------------------------

    def test_workspace_has_required_stanzas(self):
        """Verify WORKSPACE contains rules_python, python_register_toolchains, and pip_parse."""
        content = _read("examples/python-bazel/WORKSPACE")
        assert "rules_python" in content, "WORKSPACE must reference rules_python"
        assert (
            "python_register_toolchains" in content
        ), "WORKSPACE must call python_register_toolchains"
        assert "pip_parse" in content, "WORKSPACE must call pip_parse"

    def test_build_file_defines_py_binary_app(self):
        """Verify BUILD file defines py_binary named 'app', py_library, and py_test targets."""
        content = _read("examples/python-bazel/BUILD")
        assert "py_binary" in content, "BUILD must define a py_binary target"
        assert "app" in content, "BUILD py_binary must be named 'app'"
        assert "py_library" in content, "BUILD must define a py_library target"
        assert "py_test" in content, "BUILD must define a py_test target"

    def test_bazelrc_has_required_flags(self):
        """Verify .bazelrc has remote_cache, sandbox, and build:ci config."""
        content = _read("examples/python-bazel/.bazelrc")
        assert "--remote_cache" in content, ".bazelrc must define --remote_cache flag"
        has_sandbox = (
            "--sandbox" in content or "sandbox_default_allow_network" in content
        )
        assert has_sandbox, ".bazelrc must define sandbox-related flag"
        assert "build:ci" in content, ".bazelrc must define a 'build:ci' configuration"

    def test_codegen_bzl_uses_ctx_actions_run(self):
        """Verify codegen.bzl uses ctx.actions.run for code generation actions."""
        content = _read("examples/python-bazel/rules/codegen.bzl")
        assert "ctx.actions.run" in content, "codegen.bzl must use ctx.actions.run"

    # -----------------------------------------------------------------------
    # Functional checks (static)
    # -----------------------------------------------------------------------

    def test_workspace_has_no_plain_http_downloads(self):
        """Verify WORKSPACE does not use plain http:// for dependency downloads."""
        content = _read("examples/python-bazel/WORKSPACE")
        # Find all URL strings; filter out comments
        urls = re.findall(r"https?://\S+", content)
        for url in urls:
            assert not url.startswith(
                "http://"
            ), f"WORKSPACE must use https:// for downloads, found http://: {url}"

    def test_build_file_deps_reference_pip(self):
        """Verify BUILD deps reference pip-parsed packages."""
        content = _read("examples/python-bazel/BUILD")
        has_pip_dep = (
            "@pip" in content or "@pip_deps" in content or "requirement(" in content
        )
        assert has_pip_dep, "BUILD must reference pip-sourced dependencies"

    def test_workspace_has_sha256_for_external_deps(self):
        """Verify WORKSPACE external dependency downloads include sha256 hash."""
        content = _read("examples/python-bazel/WORKSPACE")
        assert (
            "sha256" in content
        ), "WORKSPACE must specify sha256 hash for at least one external dep"

    def test_codegen_bzl_declares_output_files(self):
        """Verify codegen.bzl declares output files in the rule definition."""
        content = _read("examples/python-bazel/rules/codegen.bzl")
        has_declare = "declare_file" in content or "outputs" in content
        assert has_declare, "codegen.bzl must declare output files"

    def test_build_file_no_fstrings_or_walrus(self):
        """Verify BUILD file avoids Starlark-incompatible Python syntax (f-strings, walrus)."""
        content = _read("examples/python-bazel/BUILD")
        assert (
            ":=" not in content
        ), "BUILD file must not use walrus operator := (Starlark incompatible)"
        # f-strings: check for f" or f' patterns
        assert not re.search(
            r"\bf['\"]", content
        ), "BUILD file must not use f-strings (Starlark incompatible)"

    def test_workspace_has_valid_starlark_syntax(self):
        """Verify WORKSPACE file has no obvious syntax issues (balanced parens/brackets)."""
        content = _read("examples/python-bazel/WORKSPACE")
        depth = 0
        for ch in content:
            if ch == "(":
                depth += 1
            elif ch == ")":
                depth -= 1
            if depth < 0:
                pytest.fail("WORKSPACE has unmatched closing parenthesis")
        assert depth == 0, f"WORKSPACE has {depth} unclosed parentheses"
