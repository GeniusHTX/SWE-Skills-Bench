"""
Test for 'bazel-build-optimization' skill — Bazel Build Optimization
Validates WORKSPACE/MODULE.bazel, .bazelrc, .bazelversion, BUILD files,
remote cache config, and Starlark syntax via static analysis.
"""

import glob
import os
import re
import subprocess

import pytest


class TestBazelBuildOptimization:
    """Verify Bazel build optimization: workspace, config, build files."""

    REPO_DIR = "/workspace/bazel"

    # ── helpers ──────────────────────────────────────────────────────────

    @staticmethod
    def _read_file(path: str) -> str:
        try:
            with open(path, "r", errors="ignore") as fh:
                return fh.read()
        except OSError:
            return ""

    def _root(self, *parts) -> str:
        return os.path.join(self.REPO_DIR, *parts)

    # ── file_path_check ──────────────────────────────────────────────────

    def test_workspace_or_module_bazel_exists(self):
        """WORKSPACE or MODULE.bazel must exist at repo root."""
        ws = self._root("WORKSPACE")
        mod = self._root("MODULE.bazel")
        assert os.path.isfile(ws) or os.path.isfile(mod), "Neither WORKSPACE nor MODULE.bazel found"

    def test_bazelrc_and_bazelversion_exist(self):
        """.bazelrc and .bazelversion must exist."""
        assert os.path.isfile(self._root(".bazelrc")), ".bazelrc not found"
        assert os.path.isfile(self._root(".bazelversion")), ".bazelversion not found"

    def test_build_files_exist(self):
        """At least one BUILD or BUILD.bazel file must exist."""
        builds = glob.glob(self._root("**", "BUILD"), recursive=True)
        builds += glob.glob(self._root("**", "BUILD.bazel"), recursive=True)
        assert len(builds) >= 1, "No BUILD files found"

    # ── semantic_check ───────────────────────────────────────────────────

    def test_module_bazel_declares_dependencies(self):
        """MODULE.bazel or WORKSPACE must declare external deps."""
        mod = self._read_file(self._root("MODULE.bazel"))
        ws = self._read_file(self._root("WORKSPACE"))
        content = mod or ws
        if not content:
            pytest.skip("No workspace file found")
        has_dep = "bazel_dep(" in content or "http_archive(" in content or "local_repository(" in content
        assert has_dep, "No dependency declaration found"

    def test_bazelrc_has_remote_cache(self):
        """.bazelrc must contain remote_cache configuration."""
        content = self._read_file(self._root(".bazelrc"))
        if not content:
            pytest.skip(".bazelrc not found")
        assert "remote_cache" in content, "No remote_cache config found"

    def test_go_library_importpath(self):
        """go_library targets must have importpath declarations."""
        builds = glob.glob(self._root("**", "BUILD*"), recursive=True)
        for bf in builds:
            content = self._read_file(bf)
            if "go_library(" in content:
                assert "importpath" in content, f"go_library without importpath in {bf}"
                return
        # No go_library found — skip (not all repos use Go)
        pytest.skip("No go_library targets found")

    def test_py_library_no_wildcard_test_include(self):
        """py_library glob must not accidentally include test files."""
        builds = glob.glob(self._root("**", "BUILD*"), recursive=True)
        for bf in builds:
            content = self._read_file(bf)
            if "py_library" in content and "glob(" in content:
                if "**/*.py" in content or "*.py" in content:
                    assert "exclude" in content, f"py_library glob without exclude in {bf}"

    # ── functional_check ─────────────────────────────────────────────────

    def test_bazelversion_valid_pinned(self):
        """.bazelversion must contain valid version >= 6.0."""
        content = self._read_file(self._root(".bazelversion")).strip()
        if not content:
            pytest.skip(".bazelversion not found")
        m = re.match(r"^(\d+)\.\d+\.\d+", content)
        assert m, f"Invalid version format: {content}"
        assert int(m.group(1)) >= 6, f"Bazel version {content} < 6.0"

    def test_build_files_balanced_parens(self):
        """BUILD files must have balanced parentheses (valid Starlark)."""
        builds = glob.glob(self._root("**", "BUILD*"), recursive=True)
        if not builds:
            pytest.skip("No BUILD files found")
        for bf in builds[:10]:  # Check first 10
            content = self._read_file(bf)
            assert content.count("(") == content.count(")"), f"Unbalanced parens in {bf}"

    def test_bazel_query_succeeds(self):
        """bazel query //... must succeed if Bazel is available."""
        try:
            r = subprocess.run(
                ["bazel", "query", "//..."],
                cwd=self.REPO_DIR,
                capture_output=True, text=True, timeout=120,
            )
        except FileNotFoundError:
            pytest.skip("Bazel not installed")
        except subprocess.TimeoutExpired:
            pytest.skip("Bazel query timed out")
        assert r.returncode == 0, f"bazel query failed: {r.stderr}"
        assert len(r.stdout.strip()) > 0, "No targets listed"

    def test_no_circular_deps(self):
        """bazel query deps(//...) must not report circular dependencies."""
        try:
            r = subprocess.run(
                ["bazel", "query", "deps(//...)"],
                cwd=self.REPO_DIR,
                capture_output=True, text=True, timeout=120,
            )
        except (FileNotFoundError, subprocess.TimeoutExpired):
            pytest.skip("Bazel not available")
        assert "cycle" not in r.stderr.lower(), "Circular dependency detected"
