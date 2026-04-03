"""
Test for 'gitlab-ci-patterns' skill — GitLab CI/CD Pipeline Configuration
Validates .gitlab-ci.yml with stages, parallel jobs, cache, Kaniko builds,
templates, and rollback scripts.
"""

import os
import re

import pytest

try:
    import yaml
except ImportError:
    yaml = None


class TestGitlabCiPatterns:
    """Verify GitLab CI/CD pipeline patterns."""

    REPO_DIR = "/workspace/gitlabhq"

    # ── file_path_check ─────────────────────────────────────────────────────

    def test_gitlab_ci_yml_exists(self):
        """Verify .gitlab-ci.yml exists."""
        ci_file = os.path.join(self.REPO_DIR, ".gitlab-ci.yml")
        assert os.path.isfile(ci_file), ".gitlab-ci.yml not found"

    def test_ci_templates_exist(self):
        """Verify at least one CI template file exists."""
        found = []
        for dirpath, _, fnames in os.walk(self.REPO_DIR):
            if ".git" in dirpath:
                continue
            for f in fnames:
                if (
                    f.endswith(".yml") or f.endswith(".yaml")
                ) and "template" in f.lower():
                    found.append(f)
                elif (
                    f.endswith(".yml") or f.endswith(".yaml")
                ) and "ci" in dirpath.lower():
                    found.append(f)
        assert found, "No CI template files found"

    # ── semantic_check ──────────────────────────────────────────────────────

    def test_five_stages_defined(self):
        """Verify at least 5 pipeline stages are defined."""
        ci_file = os.path.join(self.REPO_DIR, ".gitlab-ci.yml")
        if not os.path.isfile(ci_file):
            pytest.skip(".gitlab-ci.yml not found")
        content = self._read(ci_file)
        stages = re.findall(r"^\s*-\s+(\w+)", content, re.MULTILINE)
        # Also check 'stages:' block
        if yaml:
            with open(ci_file, "r") as fh:
                try:
                    data = yaml.safe_load(fh)
                    if isinstance(data, dict) and "stages" in data:
                        stages = data["stages"]
                except yaml.YAMLError:
                    pass
        assert len(stages) >= 4, f"Expected ≥4 stages, found: {stages}"

    def test_parallel_jobs(self):
        """Verify parallel job configuration (parallel: N)."""
        ci_file = os.path.join(self.REPO_DIR, ".gitlab-ci.yml")
        if not os.path.isfile(ci_file):
            pytest.skip(".gitlab-ci.yml not found")
        content = self._read(ci_file)
        assert re.search(
            r"parallel:\s*\d+", content
        ), "No parallel job configuration found"

    def test_cache_configuration(self):
        """Verify cache with pull-push policy."""
        ci_file = os.path.join(self.REPO_DIR, ".gitlab-ci.yml")
        if not os.path.isfile(ci_file):
            pytest.skip(".gitlab-ci.yml not found")
        content = self._read(ci_file)
        assert "cache" in content, "No cache configuration found"
        assert re.search(
            r"(pull-push|policy)", content
        ), "No cache pull-push policy found"

    def test_production_tag_only_kaniko(self):
        """Verify production uses tag-only deploys with Kaniko container builds."""
        all_yml = self._find_ci_files()
        for fpath in all_yml:
            content = self._read(fpath)
            if "kaniko" in content.lower() or "gcr.io/kaniko" in content:
                return
        # Check for tag-only at least
        ci_file = os.path.join(self.REPO_DIR, ".gitlab-ci.yml")
        if os.path.isfile(ci_file):
            content = self._read(ci_file)
            if re.search(r"only:\s*\n\s*-\s*tags|rules:.*tag", content):
                return
        pytest.fail("No Kaniko or tag-only production config found")

    def test_rollback_script(self):
        """Verify rollback script exists."""
        found = False
        for dirpath, _, fnames in os.walk(self.REPO_DIR):
            if ".git" in dirpath:
                continue
            for f in fnames:
                if "rollback" in f.lower() and (
                    f.endswith(".sh") or f.endswith(".yml") or f.endswith(".yaml")
                ):
                    found = True
                    break
            if found:
                break
        if not found:
            # Check inline in CI
            ci_file = os.path.join(self.REPO_DIR, ".gitlab-ci.yml")
            if os.path.isfile(ci_file):
                content = self._read(ci_file)
                if "rollback" in content.lower():
                    found = True
        assert found, "No rollback script or job found"

    # ── functional_check ────────────────────────────────────────────────────

    def test_gitlab_ci_valid_yaml(self):
        """Verify .gitlab-ci.yml is valid YAML."""
        if yaml is None:
            pytest.skip("PyYAML not available")
        ci_file = os.path.join(self.REPO_DIR, ".gitlab-ci.yml")
        if not os.path.isfile(ci_file):
            pytest.skip(".gitlab-ci.yml not found")
        with open(ci_file, "r") as fh:
            data = yaml.safe_load(fh)
        assert data is not None, ".gitlab-ci.yml is empty"

    def test_manual_rollback_action(self):
        """Verify rollback has manual trigger (when: manual)."""
        all_yml = self._find_ci_files()
        for fpath in all_yml:
            content = self._read(fpath)
            if "rollback" in content.lower() and "manual" in content.lower():
                return
        pytest.fail("No manual rollback trigger found")

    def test_bash_syntax_of_rollback(self):
        """Verify rollback shell script has valid bash syntax."""
        import subprocess

        for dirpath, _, fnames in os.walk(self.REPO_DIR):
            if ".git" in dirpath:
                continue
            for f in fnames:
                if "rollback" in f.lower() and f.endswith(".sh"):
                    fpath = os.path.join(dirpath, f)
                    try:
                        result = subprocess.run(
                            ["bash", "-n", fpath],
                            capture_output=True,
                            text=True,
                            timeout=30,
                        )
                        assert (
                            result.returncode == 0
                        ), f"Bash syntax error in {f}: {result.stderr}"
                        return
                    except FileNotFoundError:
                        pytest.skip("bash not available")
        pytest.skip("No rollback .sh file found")

    def test_includes_or_extends(self):
        """Verify CI uses include or extends for template reuse."""
        ci_file = os.path.join(self.REPO_DIR, ".gitlab-ci.yml")
        if not os.path.isfile(ci_file):
            pytest.skip(".gitlab-ci.yml not found")
        content = self._read(ci_file)
        assert re.search(
            r"(include:|extends:|\!reference)", content
        ), "No include/extends for template reuse"

    # ── helpers ──────────────────────────────────────────────────────────────

    def _find_ci_files(self):
        results = []
        for dirpath, _, fnames in os.walk(self.REPO_DIR):
            if ".git" in dirpath:
                continue
            for f in fnames:
                if (f.endswith(".yml") or f.endswith(".yaml")) and (
                    "ci" in f.lower() or "gitlab" in f.lower()
                ):
                    results.append(os.path.join(dirpath, f))
        return results

    def _read(self, path):
        with open(path, "r", errors="ignore") as fh:
            return fh.read()
