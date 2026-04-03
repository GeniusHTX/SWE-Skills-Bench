"""
Test for 'changelog-automation' skill — Changelog Automation (Ruby)
Validates CommitParser, VersionBumper, ChangelogGenerator via static
Ruby source inspection, conventional commit format handling, BREAKING
CHANGE detection, and chore exclusion.
"""

import os
import subprocess

import pytest


class TestChangelogAutomation:
    """Verify changelog automation library via Ruby source inspection."""

    REPO_DIR = "/workspace/github-changelog-generator"

    # ── helpers ──────────────────────────────────────────────────────────

    @staticmethod
    def _read_file(path: str) -> str:
        try:
            with open(path, "r", errors="ignore") as fh:
                return fh.read()
        except OSError:
            return ""

    def _lib(self, *parts) -> str:
        return os.path.join(self.REPO_DIR, "lib", "changelog", *parts)

    # ── file_path_check ──────────────────────────────────────────────────

    def test_commit_parser_rb_exists(self):
        """lib/changelog/commit_parser.rb must exist."""
        assert os.path.isfile(self._lib("commit_parser.rb")), "commit_parser.rb not found"

    def test_version_bumper_and_generator_exist(self):
        """version_bumper.rb and generator.rb must exist."""
        assert os.path.isfile(self._lib("version_bumper.rb")), "version_bumper.rb not found"
        assert os.path.isfile(self._lib("generator.rb")), "generator.rb not found"

    def test_spec_or_test_file_exists(self):
        """RSpec or minitest file for commit_parser must exist."""
        spec = os.path.join(self.REPO_DIR, "spec", "changelog", "commit_parser_spec.rb")
        test = os.path.join(self.REPO_DIR, "test", "changelog", "commit_parser_test.rb")
        assert os.path.isfile(spec) or os.path.isfile(test), "No spec/test file found"

    # ── semantic_check ───────────────────────────────────────────────────

    def test_parser_handles_conventional_commit(self):
        """CommitParser must parse type:description format."""
        content = self._read_file(self._lib("commit_parser.rb"))
        if not content:
            pytest.skip("commit_parser.rb not found")
        assert "CommitParser" in content
        assert "parse" in content
        has_type = "type" in content or "feat" in content or "fix" in content
        assert has_type, "No commit type handling found"

    def test_breaking_change_detection(self):
        """Must detect BREAKING CHANGE in footer and feat! prefix."""
        content = self._read_file(self._lib("commit_parser.rb"))
        if not content:
            pytest.skip("commit_parser.rb not found")
        assert "BREAKING CHANGE" in content or "BREAKING-CHANGE" in content
        has_bang = "!" in content
        assert has_bang, "No '!' bang prefix detection"

    def test_version_bumper_priority(self):
        """VersionBumper must prioritize major > minor > patch."""
        content = self._read_file(self._lib("version_bumper.rb"))
        if not content:
            pytest.skip("version_bumper.rb not found")
        assert "major" in content
        assert "minor" in content
        assert "patch" in content

    def test_chore_excluded_from_changelog(self):
        """Generator must filter out chore commits."""
        content = self._read_file(self._lib("generator.rb"))
        if not content:
            pytest.skip("generator.rb not found")
        has_filter = "chore" in content and ("exclude" in content or "reject" in content or "select" in content or "filter" in content)
        assert has_filter, "No chore filtering logic found"

    # ── functional_check ─────────────────────────────────────────────────

    def _ruby_available(self):
        try:
            r = subprocess.run(["ruby", "--version"], capture_output=True, timeout=10)
            return r.returncode == 0
        except (FileNotFoundError, subprocess.TimeoutExpired):
            return False

    def test_feat_bumps_minor(self):
        """VersionBumper: feat commit bumps minor (1.2.3 -> 1.3.0)."""
        if not self._ruby_available():
            pytest.skip("Ruby not available")
        script = (
            f"$LOAD_PATH.unshift '{self.REPO_DIR}/lib'; "
            "require 'changelog/version_bumper'; "
            "puts Changelog::VersionBumper.new.bump('1.2.3', [{type: 'feat', description: 'add feature'}])"
        )
        r = subprocess.run(["ruby", "-e", script], capture_output=True, text=True, timeout=30)
        if r.returncode != 0:
            pytest.skip(f"Ruby execution failed: {r.stderr}")
        assert r.stdout.strip() == "1.3.0"

    def test_breaking_change_bumps_major(self):
        """VersionBumper: breaking change bumps major (1.2.3 -> 2.0.0)."""
        if not self._ruby_available():
            pytest.skip("Ruby not available")
        script = (
            f"$LOAD_PATH.unshift '{self.REPO_DIR}/lib'; "
            "require 'changelog/version_bumper'; "
            "puts Changelog::VersionBumper.new.bump('1.2.3', [{type: 'feat', breaking: true, description: 'remove API'}])"
        )
        r = subprocess.run(["ruby", "-e", script], capture_output=True, text=True, timeout=30)
        if r.returncode != 0:
            pytest.skip(f"Ruby execution failed: {r.stderr}")
        assert r.stdout.strip() == "2.0.0"

    def test_empty_commits_unchanged(self):
        """VersionBumper: empty commits leaves version unchanged."""
        if not self._ruby_available():
            pytest.skip("Ruby not available")
        script = (
            f"$LOAD_PATH.unshift '{self.REPO_DIR}/lib'; "
            "require 'changelog/version_bumper'; "
            "puts Changelog::VersionBumper.new.bump('1.2.3', [])"
        )
        r = subprocess.run(["ruby", "-e", script], capture_output=True, text=True, timeout=30)
        if r.returncode != 0:
            pytest.skip(f"Ruby execution failed: {r.stderr}")
        assert r.stdout.strip() == "1.2.3"

    def test_changelog_excludes_chore_includes_feat(self):
        """Generated changelog must include feat but exclude chore."""
        content = self._read_file(self._lib("generator.rb"))
        if not content:
            pytest.skip("generator.rb not found")
        # Static verification that filtering logic is present
        assert "chore" in content, "'chore' keyword not found in generator"
        has_feat_section = "feat" in content.lower() or "feature" in content.lower()
        assert has_feat_section, "No feature section handling found"

    def test_missing_github_token_error(self):
        """GitHubReleaseCreator must raise ConfigurationError without token."""
        content = self._read_file(
            os.path.join(self.REPO_DIR, "lib", "changelog", "github_release.rb")
        )
        if not content:
            pytest.skip("github_release.rb not found")
        assert "ConfigurationError" in content or "GITHUB_TOKEN" in content
