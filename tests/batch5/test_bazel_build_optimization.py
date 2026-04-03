"""
Test for 'bazel-build-optimization' skill — Bazel Build Configuration
Validates WORKSPACE, .bazelrc, BUILD.bazel files, python toolchains,
pip_parse, shard_count, remote cache, and build profile configurations.
"""

import os
import re

import pytest


class TestBazelBuildOptimization:
    """Verify Bazel build optimization configuration."""

    REPO_DIR = "/workspace/bazel"

    # ── file_path_check ─────────────────────────────────────────────────────

    def test_workspace_file_exists(self):
        """Verify WORKSPACE or WORKSPACE.bazel file exists."""
        workspace_files = ["WORKSPACE", "WORKSPACE.bazel"]
        found = any(
            os.path.isfile(os.path.join(self.REPO_DIR, f)) for f in workspace_files
        )
        assert found, "No WORKSPACE or WORKSPACE.bazel file found"

    def test_bazelrc_file_exists(self):
        """Verify .bazelrc configuration file exists."""
        assert os.path.isfile(
            os.path.join(self.REPO_DIR, ".bazelrc")
        ), ".bazelrc file not found"

    def test_build_bazel_files_exist(self):
        """Verify at least 2 BUILD.bazel files exist."""
        build_files = []
        for dirpath, _, fnames in os.walk(self.REPO_DIR):
            if ".git" in dirpath:
                continue
            for f in fnames:
                if f in ("BUILD", "BUILD.bazel"):
                    build_files.append(os.path.join(dirpath, f))
        assert (
            len(build_files) >= 2
        ), f"Expected ≥2 BUILD.bazel files, found {len(build_files)}"

    # ── semantic_check ──────────────────────────────────────────────────────

    def test_python_register_toolchains(self):
        """Verify WORKSPACE registers Python toolchains."""
        content = self._read_workspace()
        if content is None:
            pytest.skip("No WORKSPACE file found")
        assert re.search(
            r"python_register_toolchains|rules_python", content
        ), "WORKSPACE does not register Python toolchains"

    def test_pip_parse_configured(self):
        """Verify pip_parse is configured for dependency management."""
        content = self._read_workspace()
        if content is None:
            pytest.skip("No WORKSPACE file found")
        assert (
            "pip_parse" in content or "pip_install" in content
        ), "No pip_parse or pip_install configuration found"

    def test_shard_count_in_build(self):
        """Verify shard_count is set for test parallelization."""
        build_files = self._find_build_files()
        assert build_files, "No BUILD files found"
        for fpath in build_files:
            content = self._read(fpath)
            if "shard_count" in content:
                return
        pytest.fail("No BUILD file uses shard_count for test parallelization")

    def test_remote_cache_in_bazelrc(self):
        """Verify .bazelrc configures remote cache for CI."""
        bazelrc = os.path.join(self.REPO_DIR, ".bazelrc")
        if not os.path.isfile(bazelrc):
            pytest.skip(".bazelrc not found")
        content = self._read(bazelrc)
        assert re.search(
            r"remote_cache|disk_cache|remote_http_cache", content
        ), ".bazelrc does not configure any caching"

    def test_build_profiles_defined(self):
        """Verify at least 2 build profiles/configs (e.g., ci, opt, dbg)."""
        bazelrc = os.path.join(self.REPO_DIR, ".bazelrc")
        if not os.path.isfile(bazelrc):
            pytest.skip(".bazelrc not found")
        content = self._read(bazelrc)
        configs = set(re.findall(r"build:(\w+)", content))
        assert len(configs) >= 2, f"Expected ≥2 build profiles, found: {configs}"

    # ── functional_check ────────────────────────────────────────────────────

    def test_workspace_parseable(self):
        """Verify WORKSPACE file has balanced parentheses."""
        content = self._read_workspace()
        if content is None:
            pytest.skip("No WORKSPACE file found")
        opens = content.count("(")
        closes = content.count(")")
        assert (
            opens == closes
        ), f"Unbalanced parentheses in WORKSPACE: ({opens} vs {closes})"

    def test_build_files_parseable(self):
        """Verify BUILD files have balanced parentheses."""
        for fpath in self._find_build_files():
            content = self._read(fpath)
            opens = content.count("(")
            closes = content.count(")")
            assert (
                opens == closes
            ), f"Unbalanced parens in {os.path.relpath(fpath, self.REPO_DIR)}"

    def test_requirements_lock_exists(self):
        """Verify a requirements lock file exists for reproducible builds."""
        found = False
        for dirpath, _, fnames in os.walk(self.REPO_DIR):
            if ".git" in dirpath:
                continue
            for f in fnames:
                if "requirements" in f.lower() and (
                    "lock" in f.lower() or "compiled" in f.lower() or f.endswith(".txt")
                ):
                    found = True
                    break
            if found:
                break
        assert found, "No requirements lock/compiled file found"

    # ── helpers ──────────────────────────────────────────────────────────────

    def _read_workspace(self):
        for name in ["WORKSPACE", "WORKSPACE.bazel"]:
            fpath = os.path.join(self.REPO_DIR, name)
            if os.path.isfile(fpath):
                return self._read(fpath)
        return None

    def _find_build_files(self):
        results = []
        for dirpath, _, fnames in os.walk(self.REPO_DIR):
            if ".git" in dirpath:
                continue
            for f in fnames:
                if f in ("BUILD", "BUILD.bazel"):
                    results.append(os.path.join(dirpath, f))
        return results

    def _read(self, path):
        with open(path, "r", errors="ignore") as fh:
            return fh.read()
