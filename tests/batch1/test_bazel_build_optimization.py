"""
Test for 'bazel-build-optimization' skill — Bazel Build Optimization
Validates that the Agent optimized Bazel build configuration with remote
caching, build parallelism, and dependency management.
"""

import os
import subprocess
import pytest


class TestBazelBuildOptimization:
    """Verify Bazel build optimization setup."""

    REPO_DIR = "/workspace/bazel"

    # ------------------------------------------------------------------
    # L1: file existence
    # ------------------------------------------------------------------

    def test_bazelrc_exists(self):
        """A .bazelrc file must exist with optimization flags."""
        fpath = os.path.join(self.REPO_DIR, ".bazelrc")
        found = os.path.isfile(fpath)
        if not found:
            # Check for user.bazelrc or ci.bazelrc
            for name in [".bazelrc", "user.bazelrc", "ci.bazelrc", ".bazelrc.user"]:
                if os.path.isfile(os.path.join(self.REPO_DIR, name)):
                    found = True
                    break
        assert found, ".bazelrc not found"

    def test_build_files_exist(self):
        """BUILD or BUILD.bazel files must exist."""
        found = False
        for root, dirs, files in os.walk(self.REPO_DIR):
            for f in files:
                if f in ("BUILD", "BUILD.bazel"):
                    found = True
                    break
            if found:
                break
        assert found, "No BUILD/BUILD.bazel files found"

    # ------------------------------------------------------------------
    # L2: content validation
    # ------------------------------------------------------------------

    def _read_bazelrc(self):
        for name in [".bazelrc", "user.bazelrc", "ci.bazelrc"]:
            fpath = os.path.join(self.REPO_DIR, name)
            if os.path.isfile(fpath):
                with open(fpath, "r") as f:
                    return f.read()
        return ""

    def test_remote_cache_config(self):
        """bazelrc should configure remote caching."""
        content = self._read_bazelrc()
        cache_patterns = [
            "remote_cache",
            "disk_cache",
            "http_cache",
            "--remote_cache",
            "--disk_cache",
        ]
        found = any(p in content for p in cache_patterns)
        assert found, "No remote/disk cache configuration in .bazelrc"

    def test_jobs_parallelism(self):
        """bazelrc should set parallelism flags."""
        content = self._read_bazelrc()
        parallel_patterns = [
            "--jobs",
            "--local_cpu_resources",
            "--local_ram_resources",
            "worker",
        ]
        found = any(p in content for p in parallel_patterns)
        assert found, "No parallelism configuration in .bazelrc"

    def test_build_config_sections(self):
        """bazelrc should define named configs (--config=ci etc.)."""
        content = self._read_bazelrc()
        config_patterns = [
            "build:ci",
            "build:opt",
            "build:remote",
            "build --config",
            "test:ci",
        ]
        found = any(p in content for p in config_patterns)
        if not found:
            # Check for any build: directives
            found = "build:" in content or "build --" in content
        assert found, "No named build configs in .bazelrc"

    def test_test_configuration(self):
        """bazelrc should configure test settings."""
        content = self._read_bazelrc()
        test_patterns = [
            "test --",
            "test:",
            "--test_output",
            "--test_timeout",
            "--flaky_test",
        ]
        found = any(p in content for p in test_patterns)
        assert found, "No test configuration in .bazelrc"

    def test_optimization_flags(self):
        """bazelrc should include compilation optimization flags."""
        content = self._read_bazelrc()
        opt_patterns = [
            "-c opt",
            "--compilation_mode",
            "--strip",
            "--copt",
            "-O2",
            "--linkopt",
            "--experimental",
            "--incompatible",
        ]
        found = any(p in content for p in opt_patterns)
        assert found, "No compilation optimization flags"

    def test_workspace_file_exists(self):
        """WORKSPACE or MODULE.bazel file must exist."""
        workspace_files = [
            "WORKSPACE",
            "WORKSPACE.bazel",
            "MODULE.bazel",
            "WORKSPACE.bzlmod",
        ]
        found = any(
            os.path.isfile(os.path.join(self.REPO_DIR, f)) for f in workspace_files
        )
        assert found, "No WORKSPACE/MODULE.bazel file found"

    def test_dependency_management(self):
        """Build must define external dependencies."""
        dep_found = False
        for fname in ["WORKSPACE", "WORKSPACE.bazel", "MODULE.bazel"]:
            fpath = os.path.join(self.REPO_DIR, fname)
            if os.path.isfile(fpath):
                with open(fpath, "r") as f:
                    content = f.read()
                dep_patterns = [
                    "http_archive",
                    "git_repository",
                    "maven_install",
                    "bazel_dep",
                    "load(",
                    "module(",
                ]
                if any(p in content for p in dep_patterns):
                    dep_found = True
                    break
        assert dep_found, "No dependency management found"

    def test_bazelrc_has_multiple_settings(self):
        """bazelrc must have at least 5 non-comment lines."""
        content = self._read_bazelrc()
        lines = [
            l.strip()
            for l in content.splitlines()
            if l.strip() and not l.strip().startswith("#")
        ]
        assert len(lines) >= 5, f".bazelrc has only {len(lines)} settings, need >= 5"
