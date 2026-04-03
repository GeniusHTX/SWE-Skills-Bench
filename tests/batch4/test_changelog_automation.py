"""
Test for 'changelog-automation' skill — Changelog Automation
Validates parse_commit (conventional commit parser) and ChangelogGenerator
with type/scope/description/breaking extraction and markdown changelog output.
"""

import os
import re
import sys
import pytest


class TestChangelogAutomation:
    """Tests for changelog automation in the github-changelog-generator repo."""

    REPO_DIR = "/workspace/github-changelog-generator"

    def _read(self, relpath):
        full = os.path.join(self.REPO_DIR, relpath)
        with open(full, "r", errors="ignore") as f:
            return f.read()

    # --- File Path Checks ---

    def test_commit_parser_py_exists(self):
        """Verifies that lib/changelog/commit_parser.py exists."""
        path = os.path.join(self.REPO_DIR, "lib", "changelog", "commit_parser.py")
        assert os.path.exists(path), f"Expected file not found: {path}"

    def test_changelog_init_py_exists(self):
        """Verifies that lib/changelog/__init__.py exists."""
        path = os.path.join(self.REPO_DIR, "lib", "changelog", "__init__.py")
        assert os.path.exists(path), f"Expected file not found: {path}"

    # --- Semantic Checks ---

    def test_sem_import_parse_commit_and_generator(self):
        """from lib.changelog.commit_parser import parse_commit, ChangelogGenerator — importable."""
        old_path = sys.path[:]
        sys.path.insert(0, self.REPO_DIR)
        try:
            from lib.changelog.commit_parser import parse_commit, ChangelogGenerator

            assert parse_commit is not None
            assert ChangelogGenerator is not None
        finally:
            sys.path[:] = old_path

    def test_sem_parse_commit_signature(self):
        """parse_commit function accepts commit_msg string parameter."""
        content = self._read("lib/changelog/commit_parser.py")
        assert re.search(
            r"def\s+parse_commit\s*\(", content
        ), "parse_commit function not defined"

    def test_sem_parsed_dict_keys(self):
        """Returned dict has keys: 'type', 'scope', 'description', 'breaking'."""
        content = self._read("lib/changelog/commit_parser.py")
        for key in ["type", "scope", "description", "breaking"]:
            assert (
                f"'{key}'" in content or f'"{key}"' in content
            ), f"Key '{key}' not found in commit_parser.py"

    def test_sem_generator_methods(self):
        """ChangelogGenerator has methods: generate, group_by_type, filter_types."""
        content = self._read("lib/changelog/commit_parser.py")
        for method in ["generate", "group_by_type", "filter_types"]:
            assert re.search(
                rf"def\s+{method}\s*\(", content
            ), f"Method {method} not found"

    # --- Functional Checks (import) ---

    def test_func_parse_simple_feat(self):
        """parse_commit('feat: add login') returns correct dict."""
        old_path = sys.path[:]
        sys.path.insert(0, self.REPO_DIR)
        try:
            from lib.changelog.commit_parser import parse_commit

            result = parse_commit("feat: add login")
            assert result == {
                "type": "feat",
                "scope": None,
                "description": "add login",
                "breaking": False,
            }
        finally:
            sys.path[:] = old_path

    def test_func_parse_fix_with_scope(self):
        """parse_commit('fix(auth): fix null pointer') returns correct dict with scope."""
        old_path = sys.path[:]
        sys.path.insert(0, self.REPO_DIR)
        try:
            from lib.changelog.commit_parser import parse_commit

            result = parse_commit("fix(auth): fix null pointer")
            assert result == {
                "type": "fix",
                "scope": "auth",
                "description": "fix null pointer",
                "breaking": False,
            }
        finally:
            sys.path[:] = old_path

    def test_func_parse_breaking_bang(self):
        """parse_commit('feat!: remove endpoint')['breaking'] == True."""
        old_path = sys.path[:]
        sys.path.insert(0, self.REPO_DIR)
        try:
            from lib.changelog.commit_parser import parse_commit

            result = parse_commit("feat!: remove endpoint")
            assert result["breaking"] is True
        finally:
            sys.path[:] = old_path

    def test_func_parse_breaking_change_footer(self):
        """BREAKING CHANGE in footer marks breaking == True."""
        old_path = sys.path[:]
        sys.path.insert(0, self.REPO_DIR)
        try:
            from lib.changelog.commit_parser import parse_commit

            result = parse_commit(
                "chore(deps): update lodash\n\nBREAKING CHANGE: requires node 18"
            )
            assert result["breaking"] is True
        finally:
            sys.path[:] = old_path

    def test_func_generator_generate_header(self):
        """ChangelogGenerator.generate produces version header in output."""
        old_path = sys.path[:]
        sys.path.insert(0, self.REPO_DIR)
        try:
            from lib.changelog.commit_parser import parse_commit, ChangelogGenerator

            gen = ChangelogGenerator([parse_commit("feat: add login")])
            out = gen.generate("1.0.0", "2024-01-01")
            assert "## [1.0.0] - 2024-01-01" in out
        finally:
            sys.path[:] = old_path

    def test_func_generator_generate_features_section(self):
        """Generated changelog contains '### Features' section."""
        old_path = sys.path[:]
        sys.path.insert(0, self.REPO_DIR)
        try:
            from lib.changelog.commit_parser import parse_commit, ChangelogGenerator

            gen = ChangelogGenerator([parse_commit("feat: add login")])
            out = gen.generate("1.0.0", "2024-01-01")
            assert "### Features" in out
        finally:
            sys.path[:] = old_path

    def test_func_generator_generate_includes_description(self):
        """Generated changelog contains the commit description."""
        old_path = sys.path[:]
        sys.path.insert(0, self.REPO_DIR)
        try:
            from lib.changelog.commit_parser import parse_commit, ChangelogGenerator

            gen = ChangelogGenerator([parse_commit("feat: add login")])
            out = gen.generate("1.0.0", "2024-01-01")
            assert "add login" in out
        finally:
            sys.path[:] = old_path

    def test_func_breaking_changes_before_features(self):
        """Breaking changes section appears before Features section in output."""
        old_path = sys.path[:]
        sys.path.insert(0, self.REPO_DIR)
        try:
            from lib.changelog.commit_parser import parse_commit, ChangelogGenerator

            gen2 = ChangelogGenerator(
                [
                    parse_commit("feat!: break"),
                    parse_commit("feat: normal"),
                ]
            )
            out2 = gen2.generate("2.0.0", "2024-01-01")
            assert out2.index("Breaking") < out2.index(
                "Features"
            ), "Breaking changes should appear before Features"
        finally:
            sys.path[:] = old_path

    def test_func_non_conventional_commit(self):
        """Non-conventional commit 'fixed some stuff' raises ValueError or returns unknown type."""
        old_path = sys.path[:]
        sys.path.insert(0, self.REPO_DIR)
        try:
            from lib.changelog.commit_parser import parse_commit

            try:
                result = parse_commit("fixed some stuff")
                # If it doesn't raise, the type should indicate unknown/other
                assert result.get("type") in (
                    None,
                    "other",
                    "unknown",
                    "",
                ), f"Expected unknown/None type for non-conventional commit, got {result.get('type')}"
            except (ValueError, KeyError):
                pass  # Expected
        finally:
            sys.path[:] = old_path
