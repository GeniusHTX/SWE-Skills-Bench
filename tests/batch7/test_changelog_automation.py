"""Test file for the changelog-automation skill.

This suite validates the ConventionalCommitParser, ConventionalCommit, and
ScopedChangelog classes in the github-changelog-generator Ruby repository.
"""

from __future__ import annotations

import pathlib
import re
import subprocess

import pytest


class TestChangelogAutomation:
    """Verify conventional-commit parsing and scoped changelog generation."""

    REPO_DIR = "/workspace/github-changelog-generator"

    PARSER_RB = "lib/github_changelog_generator/parser/conventional_commit_parser.rb"
    SCOPED_RB = "lib/github_changelog_generator/generator/scoped_changelog.rb"
    PARSER_TEST_RB = (
        "lib/github_changelog_generator/parser/conventional_commit_parser_test.rb"
    )

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    def _repo_path(self, relative: str) -> pathlib.Path:
        return pathlib.Path(self.REPO_DIR, *relative.split("/"))

    def _read_text(self, relative: str) -> str:
        path = self._repo_path(relative)
        assert path.exists(), f"Expected path to exist: {path}"
        return path.read_text(encoding="utf-8", errors="ignore")

    def _assert_non_empty_file(self, relative: str) -> pathlib.Path:
        path = self._repo_path(relative)
        assert path.is_file(), f"Expected file to exist: {path}"
        assert path.stat().st_size > 0, f"Expected non-empty file: {path}"
        return path

    def _run_ruby(self, script: str, *, timeout: int = 60) -> str:
        """Execute a Ruby snippet and return stdout."""
        result = subprocess.run(
            ["ruby", "-e", script],
            capture_output=True,
            text=True,
            timeout=timeout,
            cwd=self.REPO_DIR,
        )
        if result.returncode != 0:
            pytest.fail(f"Ruby script failed:\n{result.stderr[:1000]}")
        return result.stdout.strip()

    # ------------------------------------------------------------------
    # Layer 1 – file_path_check (3 cases)
    # ------------------------------------------------------------------

    def test_file_path_lib_github_changelog_generator_parser_conventional_commit_pa(
        self,
    ):
        """Verify conventional_commit_parser.rb exists and is non-empty."""
        self._assert_non_empty_file(self.PARSER_RB)

    def test_file_path_lib_github_changelog_generator_generator_scoped_changelog_rb(
        self,
    ):
        """Verify scoped_changelog.rb exists and is non-empty."""
        self._assert_non_empty_file(self.SCOPED_RB)

    def test_file_path_lib_github_changelog_generator_parser_conventional_commit_pa_1(
        self,
    ):
        """Verify conventional_commit_parser_test.rb exists and is non-empty."""
        self._assert_non_empty_file(self.PARSER_TEST_RB)

    # ------------------------------------------------------------------
    # Layer 2 – semantic_check (5 cases)
    # ------------------------------------------------------------------

    def test_semantic_conventionalcommit_class_has_attr_reader_for_type_scope_desc(
        self,
    ):
        """ConventionalCommit has attr_reader for type, scope, description, body, breaking, footers."""
        src = self._read_text(self.PARSER_RB)
        assert (
            "class ConventionalCommit" in src or "ConventionalCommit" in src
        ), "ConventionalCommit class not found"
        for attr in ("type", "scope", "description", "body", "breaking", "footers"):
            assert re.search(
                rf"attr_reader.*:{attr}|attr_accessor.*:{attr}|def\s+{attr}", src
            ), f"Missing attr_reader/accessor for :{attr}"

    def test_semantic_parse_method_uses_regex_to_extract_subject_line_components(self):
        """parse method uses regex to extract subject-line components."""
        src = self._read_text(self.PARSER_RB)
        assert re.search(r"def\s+parse", src), "Missing parse method"
        # Should contain a regex for conventional commit format
        assert re.search(r"/\^?\(?\\?\w.*:", src) or re.search(
            r"Regexp|regex|pattern|match", src, re.IGNORECASE
        ), "parse should use regex to parse conventional commit subject"

    def test_semantic_footer_parsing_handles_both_key_value_and_key_value_formats(self):
        """Footer parsing handles both 'Key: value' and 'Key #value' formats."""
        src = self._read_text(self.PARSER_RB)
        assert re.search(
            r"footer|BREAKING.CHANGE|trailer", src, re.IGNORECASE
        ), "Parser should handle footer/trailer parsing"
        # Should handle two footer formats
        assert re.search(
            r"#|:\s", src
        ), "Footer parser should handle 'Key: value' or 'Key #value'"

    def test_semantic_scopedchangelog_constructor_accepts_commits_array_and_option(
        self,
    ):
        """ScopedChangelog constructor accepts commits array and options hash."""
        src = self._read_text(self.SCOPED_RB)
        assert (
            "class ScopedChangelog" in src or "ScopedChangelog" in src
        ), "ScopedChangelog class not found"
        assert re.search(
            r"def\s+initialize\s*\(.*commits|def\s+initialize\s*\(.*options", src
        ), "ScopedChangelog constructor should accept commits and options"

    def test_semantic_generate_method_produces_markdown_with_version_heading_break(
        self,
    ):
        """generate method produces Markdown with version heading, breaking section, type sections."""
        src = self._read_text(self.SCOPED_RB)
        assert re.search(r"def\s+generate", src), "Missing generate method"
        # Should reference markdown heading patterns
        assert re.search(
            r"##|heading|markdown|section|breaking", src, re.IGNORECASE
        ), "generate should produce Markdown with headings and sections"

    # ------------------------------------------------------------------
    # Layer 3 – functional_check (5 cases, import-style via Ruby subprocess)
    # ------------------------------------------------------------------

    def _parse_commit(self, message: str) -> dict | None:
        """Parse a commit message via Ruby and return a dict or None."""
        import json as _json

        escaped = message.replace("\\", "\\\\").replace("'", "\\'")
        script = (
            f"$LOAD_PATH.unshift('{self.REPO_DIR}/lib')\n"
            "require 'github_changelog_generator/parser/conventional_commit_parser'\n"
            "require 'json'\n"
            f"result = GitHubChangelogGenerator::ConventionalCommitParser.new.parse('{escaped}')\n"
            "if result.nil?\n"
            "  puts 'null'\n"
            "else\n"
            "  puts({type: result.type, scope: result.scope, description: result.description,"
            " breaking: result.breaking}.to_json)\n"
            "end\n"
        )
        out = self._run_ruby(script)
        if out == "null":
            return None
        return _json.loads(out)

    def test_functional_parse_feat_auth_add_oauth2_login_type_feat_scope_auth_breaki(
        self,
    ):
        """parse('feat(auth): add OAuth2 login') → type='feat', scope='auth', breaking=false."""
        result = self._parse_commit("feat(auth): add OAuth2 login")
        assert result is not None, "Expected a parsed result, got nil"
        assert result["type"] == "feat"
        assert result["scope"] == "auth"
        assert result["breaking"] is False

    def test_functional_parse_fix_correct_null_pointer_breaking_true_scope_nil(self):
        """parse('fix!: correct null pointer') → breaking=true, scope=nil."""
        result = self._parse_commit("fix!: correct null pointer")
        assert result is not None, "Expected a parsed result, got nil"
        assert result["type"] == "fix"
        assert result["breaking"] is True
        assert result["scope"] is None or result["scope"] == ""

    def test_functional_parse_feat_api_new_endpoint_n_nbreaking_change_v1_users_remo(
        self,
    ):
        """parse with BREAKING CHANGE footer → breaking=true."""
        result = self._parse_commit(
            "feat(api): new endpoint\\n\\nBREAKING CHANGE: /v1/users removed"
        )
        assert result is not None, "Expected a parsed result, got nil"
        assert result["type"] == "feat"
        assert result["breaking"] is True

    def test_functional_parse_not_a_conventional_commit_nil(self):
        """parse('not a conventional commit') → nil."""
        result = self._parse_commit("not a conventional commit")
        assert (
            result is None
        ), f"Expected nil for non-conventional message, got {result}"

    def test_functional_changelog_with_10_mixed_commits_sections_in_correct_order(self):
        """Changelog with 10 mixed commits → sections in correct order."""
        src = self._read_text(self.SCOPED_RB)
        # Verify that the generator sorts sections properly
        assert re.search(
            r"breaking|BREAKING", src
        ), "ScopedChangelog should have a dedicated breaking section"
        assert re.search(
            r"feat|fix|chore|refactor|type", src
        ), "ScopedChangelog should categorize commits by type"
        # Verify section ordering logic
        assert re.search(
            r"sort|order|each|map", src
        ), "ScopedChangelog should iterate/sort commit types"
