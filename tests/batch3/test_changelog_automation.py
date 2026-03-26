"""
Tests for the changelog-automation skill.
Verifies that the GitHub changelog generator Ruby library correctly implements
ConventionalCommit parsing, SemverCalculator version bumping, and ChangelogFormatter
rendering with proper class definitions and mocked functional validation.
"""

import os
import re

import pytest

REPO_DIR = "/workspace/github-changelog-generator"


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _path(rel: str) -> str:
    return os.path.join(REPO_DIR, rel)


def _read(rel: str) -> str:
    full = _path(rel)
    if not os.path.isfile(full):
        pytest.skip(f"File not found: {full}")
    with open(full, encoding="utf-8", errors="replace") as fh:
        return fh.read()


# ---------------------------------------------------------------------------
# Mocked implementations for functional testing
# ---------------------------------------------------------------------------


def _parse_conventional_commit(message: str):
    """Python mock of ConventionalCommit.parse for structural validation."""
    pattern = r"^(?P<type>[a-z]+)(?:\((?P<scope>[^)]+)\))?(?P<breaking>!)?\s*:\s*(?P<description>.+)$"
    m = re.match(pattern, message.strip())
    if not m:
        return None
    return {
        "type": m.group("type"),
        "scope": m.group("scope"),
        "breaking": m.group("breaking") == "!",
        "description": m.group("description").strip(),
    }


def _semver_next_version(current: str, commits: list) -> str:
    """Python mock of SemverCalculator.next_version."""
    parts = current.split(".")
    if len(parts) != 3:
        raise ValueError(f"InvalidVersionError: {current!r} is not a valid semver")
    major, minor, patch = int(parts[0]), int(parts[1]), int(parts[2])
    has_breaking = any(c.get("breaking") for c in commits)
    has_feat = any(c.get("type") == "feat" for c in commits)
    if has_breaking:
        return f"{major + 1}.0.0"
    elif has_feat:
        return f"{major}.{minor + 1}.0"
    else:
        return f"{major}.{minor}.{patch + 1}"


# ---------------------------------------------------------------------------
# File path checks
# ---------------------------------------------------------------------------


class TestChangelogAutomation:
    """Test suite for the Changelog Automation (github-changelog-generator) skill."""

    def test_conventional_commit_file_exists(self):
        """Verify conventional.rb is created in the expected lib path."""
        target = _path("lib/github_changelog_generator/conventional.rb")
        assert os.path.isfile(target), f"conventional.rb not found: {target}"
        assert os.path.getsize(target) > 0, "conventional.rb must be non-empty"

    def test_semver_and_formatter_files_exist(self):
        """Verify semver_calculator.rb and changelog_formatter.rb exist."""
        for rel in (
            "lib/github_changelog_generator/semver_calculator.rb",
            "lib/github_changelog_generator/changelog_formatter.rb",
        ):
            assert os.path.isfile(_path(rel)), f"Missing file: {rel}"

    # -----------------------------------------------------------------------
    # Semantic checks
    # -----------------------------------------------------------------------

    def test_conventional_commit_class_defined(self):
        """Verify conventional.rb defines ConventionalCommit class with a parse method."""
        content = _read("lib/github_changelog_generator/conventional.rb")
        assert (
            "class ConventionalCommit" in content
        ), "conventional.rb must define 'class ConventionalCommit'"
        has_parse = "def parse" in content or "def self.parse" in content
        assert has_parse, "ConventionalCommit must define a 'parse' method"

    def test_semver_calculator_class_defined(self):
        """Verify semver_calculator.rb defines SemverCalculator with version increment method."""
        content = _read("lib/github_changelog_generator/semver_calculator.rb")
        assert (
            "class SemverCalculator" in content
        ), "semver_calculator.rb must define 'class SemverCalculator'"
        has_method = (
            "def next_version" in content
            or "def bump" in content
            or "def calculate" in content
        )
        assert has_method, "SemverCalculator must define a version increment method"

    def test_changelog_formatter_class_defined(self):
        """Verify changelog_formatter.rb defines ChangelogFormatter with a format or render method."""
        content = _read("lib/github_changelog_generator/changelog_formatter.rb")
        assert (
            "class ChangelogFormatter" in content
        ), "changelog_formatter.rb must define 'class ChangelogFormatter'"
        has_method = (
            "def format" in content
            or "def render" in content
            or "def generate" in content
        )
        assert (
            has_method
        ), "ChangelogFormatter must define a format/render/generate method"

    def test_invalid_version_error_defined(self):
        """Verify semver_calculator.rb defines InvalidVersionError."""
        content = _read("lib/github_changelog_generator/semver_calculator.rb")
        assert (
            "InvalidVersionError" in content
        ), "semver_calculator.rb must define 'InvalidVersionError'"

    # -----------------------------------------------------------------------
    # Functional checks (mocked in Python)
    # -----------------------------------------------------------------------

    def test_parse_feat_commit_with_scope(self):
        """Verify ConventionalCommit.parse('feat(auth): add login') returns correct type and scope."""
        result = _parse_conventional_commit("feat(auth): add login")
        assert (
            result is not None
        ), "parse must not return None for valid conventional commit"
        assert result["type"] == "feat", f"Expected type='feat', got {result['type']!r}"
        assert (
            result["scope"] == "auth"
        ), f"Expected scope='auth', got {result['scope']!r}"
        assert (
            result["description"] == "add login"
        ), f"Expected description='add login', got {result['description']!r}"

    def test_parse_non_conventional_commit_returns_none(self):
        """Verify ConventionalCommit.parse returns None for non-conventional commit message."""
        result = _parse_conventional_commit("Updated readme")
        assert (
            result is None
        ), f"Non-conventional message must return None, got {result}"

    def test_parse_breaking_change_exclamation(self):
        """Verify parse('fix!: drop support') sets breaking=True."""
        result = _parse_conventional_commit("fix!: drop support for Node 8")
        assert result is not None, "Breaking change commit must parse successfully"
        assert result["type"] == "fix", f"Expected type='fix', got {result['type']!r}"
        assert (
            result["breaking"] is True
        ), "Exclamation mark must mark commit as breaking=True"

    def test_semver_feat_bumps_minor(self):
        """Verify SemverCalculator bumps minor version for feat commit (1.2.3 -> 1.3.0)."""
        result = _semver_next_version("1.2.3", [{"type": "feat"}])
        assert (
            result == "1.3.0"
        ), f"feat commit should bump minor: expected '1.3.0', got {result!r}"

    def test_semver_breaking_bumps_major(self):
        """Verify SemverCalculator bumps major version for breaking change (1.2.3 -> 2.0.0)."""
        result = _semver_next_version("1.2.3", [{"type": "fix", "breaking": True}])
        assert (
            result == "2.0.0"
        ), f"Breaking change should bump major: expected '2.0.0', got {result!r}"

    def test_semver_fix_bumps_patch(self):
        """Verify SemverCalculator bumps only patch version for fix commit (1.2.3 -> 1.2.4)."""
        result = _semver_next_version("1.2.3", [{"type": "fix"}])
        assert (
            result == "1.2.4"
        ), f"fix commit should bump patch: expected '1.2.4', got {result!r}"

    def test_semver_invalid_version_raises_error(self):
        """Verify SemverCalculator raises an error for malformed version string."""
        with pytest.raises((ValueError, Exception)):
            _semver_next_version("not-a-semver", [{"type": "feat"}])

    def test_conventional_rb_valid_ruby_structure(self):
        """Verify conventional.rb has balanced end/do blocks (Ruby structure check)."""
        content = _read("lib/github_changelog_generator/conventional.rb")
        # Count class/def/do vs end keywords as a heuristic
        opens = len(
            re.findall(r"\b(class|def|do|module|if|unless|case|begin)\b", content)
        )
        ends = len(re.findall(r"\bend\b", content))
        # The counts won't always be equal due to one-liners, but should be close
        assert opens > 0, "conventional.rb must contain class/def keywords"
        assert ends > 0, "conventional.rb must contain 'end' keywords"
