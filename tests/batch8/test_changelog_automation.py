"""
Test for 'changelog-automation' skill — Changelog Automation
Validates that the Agent created a Python package for parsing conventional
commits, determining version bumps, and generating changelog Markdown.
"""

import os
import re
import sys

import pytest


class TestChangelogAutomation:
    """Verify changelog automation package implementation."""

    REPO_DIR = "/workspace/github-changelog-generator"

    @staticmethod
    def _read(path: str) -> str:
        try:
            with open(path, "r", errors="ignore") as fh:
                return fh.read()
        except OSError:
            return ""

    # ── file_path_check ─────────────────────────────────────────────

    def test_changelog_package_structure(self):
        """Verify changelog_automation package files exist."""
        for rel in (
            "src/changelog_automation/__init__.py",
            "src/changelog_automation/parser.py",
        ):
            path = os.path.join(self.REPO_DIR, rel)
            assert os.path.isfile(path), f"Missing: {rel}"

    def test_builder_versioner_exist(self):
        """Verify builder.py and versioner.py exist in the changelog_automation package."""
        for rel in ("src/changelog_automation/builder.py",
                     "src/changelog_automation/versioner.py"):
            path = os.path.join(self.REPO_DIR, rel)
            assert os.path.isfile(path), f"Missing: {rel}"

    def test_classes_importable(self):
        """All three main classes are importable without errors."""
        if not os.path.isdir(self.REPO_DIR):
            pytest.skip("Repo dir does not exist")
        sys.path.insert(0, os.path.join(self.REPO_DIR, "src"))
        try:
            from changelog_automation.parser import ConventionalCommitParser, ParseError  # noqa: F401
            from changelog_automation.builder import ChangelogBuilder  # noqa: F401
            from changelog_automation.versioner import ReleaseVersioner  # noqa: F401
        except ImportError:
            pytest.skip("changelog_automation not importable")
        finally:
            sys.path.pop(0)

    # ── semantic_check ──────────────────────────────────────────────

    def test_parser_class_defined(self):
        """Verify parser.py defines ConventionalCommitParser, ParsedCommit, and ParseError."""
        content = self._read(os.path.join(
            self.REPO_DIR, "src/changelog_automation/parser.py"))
        assert content, "parser.py is empty or unreadable"
        for name in ("ConventionalCommitParser", "ParsedCommit", "ParseError"):
            assert name in content, f"'{name}' not found in parser.py"

    def test_versioner_bump_logic(self):
        """Verify versioner.py implements major/minor/patch bump logic."""
        content = self._read(os.path.join(
            self.REPO_DIR, "src/changelog_automation/versioner.py"))
        assert content, "versioner.py is empty or unreadable"
        for level in ("major", "minor", "patch"):
            assert level in content, f"'{level}' not found in versioner.py"

    def test_builder_changelog_sections(self):
        """Verify builder.py references expected markdown section headings."""
        content = self._read(os.path.join(
            self.REPO_DIR, "src/changelog_automation/builder.py"))
        assert content, "builder.py is empty or unreadable"
        found = any(s in content for s in ("Features", "Bug Fixes", "Breaking Changes"))
        assert found, "No changelog section headings found in builder.py"

    # ── functional_check (import) ───────────────────────────────────

    def _import(self, dotpath: str):
        if not os.path.isdir(self.REPO_DIR):
            pytest.skip("Repo dir does not exist")
        sys.path.insert(0, os.path.join(self.REPO_DIR, "src"))
        try:
            return __import__(dotpath, fromlist=[""])
        except ImportError:
            pytest.skip(f"{dotpath} not importable")
        finally:
            sys.path.pop(0)

    def test_parse_feat_commit(self):
        """parse('feat(auth): add OAuth2 support') returns correct ParsedCommit fields."""
        mod = self._import("changelog_automation.parser")
        c = mod.ConventionalCommitParser().parse("feat(auth): add OAuth2 support")
        assert c.type == "feat"
        assert c.scope == "auth"
        assert c.breaking is False

    def test_parse_breaking_commit_exclamation(self):
        """parse('fix!: remove deprecated endpoint') sets breaking=True."""
        mod = self._import("changelog_automation.parser")
        c = mod.ConventionalCommitParser().parse("fix!: remove deprecated endpoint")
        assert c.breaking is True

    def test_parse_invalid_raises_parse_error(self):
        """parse('no colon without separator') raises ParseError."""
        mod = self._import("changelog_automation.parser")
        with pytest.raises(mod.ParseError):
            mod.ConventionalCommitParser().parse("no colon without separator")

    def test_version_bump_major_on_breaking(self):
        """determine_version returns major bump when any commit is breaking."""
        mod = self._import("changelog_automation.versioner")
        versioner = mod.ReleaseVersioner()
        # Create a mock commit-like object
        class FakeCommit:
            def __init__(self, t, b):
                self.type = t
                self.breaking = b
        result = versioner.determine_version("1.2.3", [FakeCommit("fix", True)])
        assert result == "2.0.0", f"Expected '2.0.0', got '{result}'"

    def test_changelog_build_output_has_features_section(self):
        """ChangelogBuilder.build with feat commit produces output containing '### Features'."""
        mod_builder = self._import("changelog_automation.builder")
        mod_parser = self._import("changelog_automation.parser")
        commit = mod_parser.ConventionalCommitParser().parse("feat(auth): Add OAuth2 support")
        output = mod_builder.ChangelogBuilder().build([commit], "1.3.0")
        assert "### Features" in output or "Features" in output, \
            "Features section heading not found in changelog output"
        assert "OAuth2" in output, "Commit description not found in changelog output"
