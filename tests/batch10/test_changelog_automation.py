"""
Test for 'changelog-automation' skill — GitHub Changelog Generator Automation
Validates that the Agent implemented changelog automation with Ruby commit parser,
version calculator, and changelog renderer.
"""

import os
import re

import pytest


class TestChangelogAutomation:
    """Verify changelog automation implementation."""

    REPO_DIR = "/workspace/github-changelog-generator"

    def test_commit_parser_exists(self):
        """Commit parser module must exist."""
        found = False
        for root, dirs, files in os.walk(self.REPO_DIR):
            for f in files:
                if f.endswith(".rb") and ("parser" in f.lower() or "commit" in f.lower()):
                    found = True
                    break
            if found:
                break
        assert found, "Commit parser module not found"

    def test_version_calculator_exists(self):
        """Version calculator module must exist."""
        found = False
        for root, dirs, files in os.walk(self.REPO_DIR):
            for f in files:
                if f.endswith(".rb") and ("version" in f.lower()):
                    found = True
                    break
            if found:
                break
        assert found, "Version calculator module not found"

    def test_changelog_renderer_exists(self):
        """Changelog renderer module must exist."""
        found = False
        for root, dirs, files in os.walk(self.REPO_DIR):
            for f in files:
                if f.endswith(".rb") and ("render" in f.lower() or "generat" in f.lower() or "changelog" in f.lower()):
                    found = True
                    break
            if found:
                break
        assert found, "Changelog renderer not found"

    def test_parser_extracts_conventional_commits(self):
        """Parser must extract conventional commit types (feat, fix, etc.)."""
        found = False
        for root, dirs, files in os.walk(self.REPO_DIR):
            for f in files:
                if f.endswith(".rb"):
                    path = os.path.join(root, f)
                    with open(path, "r", errors="ignore") as fh:
                        content = fh.read()
                    if re.search(r"feat|fix|chore|breaking", content) and re.search(r"parse|commit|conventional", content, re.IGNORECASE):
                        found = True
                        break
            if found:
                break
        assert found, "Parser does not extract conventional commit types"

    def test_version_follows_semver(self):
        """Version calculator must use semantic versioning (major.minor.patch)."""
        found = False
        for root, dirs, files in os.walk(self.REPO_DIR):
            for f in files:
                if f.endswith(".rb"):
                    path = os.path.join(root, f)
                    with open(path, "r", errors="ignore") as fh:
                        content = fh.read()
                    if re.search(r"major|minor|patch|semver|semantic", content, re.IGNORECASE):
                        found = True
                        break
            if found:
                break
        assert found, "Version calculator does not use semver"

    def test_breaking_change_bumps_major(self):
        """Breaking changes should trigger a major version bump."""
        found = False
        for root, dirs, files in os.walk(self.REPO_DIR):
            for f in files:
                if f.endswith(".rb"):
                    path = os.path.join(root, f)
                    with open(path, "r", errors="ignore") as fh:
                        content = fh.read()
                    if re.search(r"break|BREAKING", content) and re.search(r"major", content, re.IGNORECASE):
                        found = True
                        break
            if found:
                break
        assert found, "Breaking changes do not bump major version"

    def test_renderer_outputs_markdown(self):
        """Renderer must output Markdown-formatted changelog."""
        found = False
        for root, dirs, files in os.walk(self.REPO_DIR):
            for f in files:
                if f.endswith(".rb"):
                    path = os.path.join(root, f)
                    with open(path, "r", errors="ignore") as fh:
                        content = fh.read()
                    if re.search(r"markdown|\.md|##\s|###\s|\*\s", content, re.IGNORECASE):
                        found = True
                        break
            if found:
                break
        assert found, "Renderer does not output Markdown"

    def test_changelog_groups_by_type(self):
        """Changelog must group entries by type (Features, Bug Fixes, etc.)."""
        found = False
        for root, dirs, files in os.walk(self.REPO_DIR):
            for f in files:
                if f.endswith(".rb"):
                    path = os.path.join(root, f)
                    with open(path, "r", errors="ignore") as fh:
                        content = fh.read()
                    if re.search(r"group|section|categor|Features|Bug\s*Fix", content, re.IGNORECASE):
                        found = True
                        break
            if found:
                break
        assert found, "Changelog does not group by type"

    def test_git_log_integration(self):
        """Module must integrate with git log for commit retrieval."""
        found = False
        for root, dirs, files in os.walk(self.REPO_DIR):
            for f in files:
                if f.endswith(".rb"):
                    path = os.path.join(root, f)
                    with open(path, "r", errors="ignore") as fh:
                        content = fh.read()
                    if re.search(r"git.*log|`git|system.*git|Octokit|GitHub", content):
                        found = True
                        break
            if found:
                break
        assert found, "No git log integration found"

    def test_tests_exist(self):
        """Tests for changelog automation must exist."""
        found = False
        test_dirs = [
            os.path.join(self.REPO_DIR, "spec"),
            os.path.join(self.REPO_DIR, "test"),
        ]
        for test_dir in test_dirs:
            if os.path.isdir(test_dir):
                for root, dirs, files in os.walk(test_dir):
                    for f in files:
                        if f.endswith((".rb", ".py")):
                            found = True
                            break
                    if found:
                        break
            if found:
                break
        assert found, "No test files found"

    def test_date_formatting_in_changelog(self):
        """Changelog entries should include formatted dates."""
        found = False
        for root, dirs, files in os.walk(self.REPO_DIR):
            for f in files:
                if f.endswith(".rb"):
                    path = os.path.join(root, f)
                    with open(path, "r", errors="ignore") as fh:
                        content = fh.read()
                    if re.search(r"strftime|date|Time\.|Date\.", content):
                        found = True
                        break
            if found:
                break
        assert found, "No date formatting in changelog"
