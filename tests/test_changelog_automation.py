"""
Test for 'changelog-automation' skill — Changelog Generation Automation
Validates that the Agent configured automatic changelog generation from
git commit history using github-changelog-generator conventions.
"""

import os
import subprocess
import pytest


class TestChangelogAutomation:
    """Verify changelog automation setup."""

    REPO_DIR = "/workspace/github-changelog-generator"

    # ------------------------------------------------------------------
    # L1: file existence
    # ------------------------------------------------------------------

    def test_config_file_exists(self):
        """A changelog configuration file must exist."""
        config_names = [
            ".github_changelog_generator",
            ".changelog.yml",
            ".changelog.yaml",
            "changelog.config.js",
            ".chglog/config.yml",
        ]
        found = False
        for name in config_names:
            if os.path.isfile(os.path.join(self.REPO_DIR, name)):
                found = True
                break
        if not found:
            # Search recursively
            for root, dirs, files in os.walk(self.REPO_DIR):
                for f in files:
                    if "changelog" in f.lower() and (
                        f.endswith((".yml", ".yaml", ".json", ".rb", ".js"))
                    ):
                        found = True
                        break
                if found:
                    break
        assert found, "No changelog configuration file found"

    def test_template_exists(self):
        """A changelog template or script must exist."""
        found = []
        for root, dirs, files in os.walk(self.REPO_DIR):
            for f in files:
                if "changelog" in f.lower() and (
                    f.endswith((".md", ".erb", ".mustache", ".hbs", ".tpl"))
                    or "template" in f.lower()
                ):
                    found.append(os.path.join(root, f))
        assert len(found) >= 1, "No changelog template found"

    # ------------------------------------------------------------------
    # L2: content validation
    # ------------------------------------------------------------------

    def test_config_has_sections(self):
        """Config must define change categories (added, fixed, etc.)."""
        config_content = ""
        for root, dirs, files in os.walk(self.REPO_DIR):
            for f in files:
                if "changelog" in f.lower() and f.endswith(
                    (".yml", ".yaml", ".json", ".rb")
                ):
                    fpath = os.path.join(root, f)
                    with open(fpath, "r", errors="ignore") as fh:
                        config_content += fh.read() + "\n"
        categories = [
            "added",
            "changed",
            "deprecated",
            "removed",
            "fixed",
            "security",
            "bug",
            "feature",
            "enhancement",
            "breaking",
        ]
        found = sum(1 for c in categories if c in config_content.lower())
        assert found >= 3, f"Only {found} changelog categories found, need >= 3"

    def test_git_integration(self):
        """Config must reference git-based changelog generation."""
        found = False
        for root, dirs, files in os.walk(self.REPO_DIR):
            for f in files:
                if "changelog" in f.lower():
                    fpath = os.path.join(root, f)
                    with open(fpath, "r", errors="ignore") as fh:
                        content = fh.read()
                    git_patterns = [
                        "git",
                        "commit",
                        "tag",
                        "merge",
                        "pull_request",
                        "issue",
                        "label",
                    ]
                    if any(p in content.lower() for p in git_patterns):
                        found = True
                        break
            if found:
                break
        assert found, "No git integration in changelog config"

    def test_output_format(self):
        """Changelog must be in Markdown format."""
        found = False
        for root, dirs, files in os.walk(self.REPO_DIR):
            for f in files:
                if f.upper() == "CHANGELOG.MD" or (
                    "changelog" in f.lower() and f.endswith(".md")
                ):
                    found = True
                    break
            if found:
                break
        if not found:
            # Check if config references markdown output
            for root, dirs, files in os.walk(self.REPO_DIR):
                for f in files:
                    if "changelog" in f.lower():
                        fpath = os.path.join(root, f)
                        with open(fpath, "r", errors="ignore") as fh:
                            content = fh.read()
                        if "markdown" in content.lower() or ".md" in content:
                            found = True
                            break
                if found:
                    break
        assert found, "No Markdown changelog output found"

    def test_version_extraction(self):
        """Config or script must handle version extraction from tags."""
        found = False
        for root, dirs, files in os.walk(self.REPO_DIR):
            for f in files:
                if "changelog" in f.lower():
                    fpath = os.path.join(root, f)
                    with open(fpath, "r", errors="ignore") as fh:
                        content = fh.read()
                    version_markers = [
                        "version",
                        "tag",
                        "semver",
                        "release",
                        "since_tag",
                        "future_release",
                    ]
                    if any(m in content.lower() for m in version_markers):
                        found = True
                        break
            if found:
                break
        assert found, "No version extraction mechanism found"

    def test_label_mapping(self):
        """Config should map PR labels to changelog sections."""
        found = False
        for root, dirs, files in os.walk(self.REPO_DIR):
            for f in files:
                if "changelog" in f.lower() and f.endswith(
                    (".yml", ".yaml", ".json", ".rb")
                ):
                    fpath = os.path.join(root, f)
                    with open(fpath, "r", errors="ignore") as fh:
                        content = fh.read()
                    label_patterns = [
                        "label",
                        "section",
                        "category",
                        "enhancement_label",
                        "bug_label",
                    ]
                    if any(p in content.lower() for p in label_patterns):
                        found = True
                        break
            if found:
                break
        assert found, "No label-to-section mapping found"

    def test_ci_integration(self):
        """GitHub Actions or CI workflow for changelog generation."""
        found = False
        ci_dirs = [
            os.path.join(self.REPO_DIR, ".github", "workflows"),
            os.path.join(self.REPO_DIR, ".circleci"),
            os.path.join(self.REPO_DIR, ".travis.yml"),
        ]
        for ci_dir in ci_dirs:
            if os.path.isdir(ci_dir):
                for f in os.listdir(ci_dir):
                    fpath = os.path.join(ci_dir, f)
                    if os.path.isfile(fpath):
                        with open(fpath, "r", errors="ignore") as fh:
                            content = fh.read()
                        if "changelog" in content.lower():
                            found = True
                            break
            if found:
                break
        # Also check Rakefile or Gemfile
        for fname in ["Rakefile", "Gemfile"]:
            fpath = os.path.join(self.REPO_DIR, fname)
            if os.path.isfile(fpath):
                with open(fpath, "r", errors="ignore") as fh:
                    content = fh.read()
                if "changelog" in content.lower():
                    found = True
                    break
        assert found, "No CI integration for changelog"

    def test_exclusion_patterns(self):
        """Config should define exclusion patterns."""
        found = False
        for root, dirs, files in os.walk(self.REPO_DIR):
            for f in files:
                if "changelog" in f.lower() and f.endswith(
                    (".yml", ".yaml", ".json", ".rb")
                ):
                    fpath = os.path.join(root, f)
                    with open(fpath, "r", errors="ignore") as fh:
                        content = fh.read()
                    exclude_patterns = [
                        "exclude",
                        "ignore",
                        "filter",
                        "skip",
                        "exclude_labels",
                    ]
                    if any(p in content.lower() for p in exclude_patterns):
                        found = True
                        break
            if found:
                break
        assert found, "No exclusion patterns found in config"

    def test_at_least_3_config_options(self):
        """Config must have at least 3 meaningful settings."""
        for root, dirs, files in os.walk(self.REPO_DIR):
            for f in files:
                if "changelog" in f.lower() and f.endswith(
                    (".yml", ".yaml", ".json", ".rb")
                ):
                    fpath = os.path.join(root, f)
                    with open(fpath, "r") as fh:
                        lines = [
                            l.strip()
                            for l in fh.readlines()
                            if l.strip() and not l.strip().startswith("#")
                        ]
                    if len(lines) >= 3:
                        return
        pytest.fail("Config has fewer than 3 meaningful settings")
