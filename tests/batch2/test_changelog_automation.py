"""
Test for 'changelog-automation' skill — GitHub Changelog Generator Extensions
Validates that the Agent created/modified section_config.rb for label-to-section
mapping, formatter/keep_a_changelog.rb for Keep-a-Changelog formatting, and
.github_changelog_generator config file with valid Ruby syntax.
"""

import os
import re
import subprocess

import pytest


class TestChangelogAutomation:
    """Verify changelog generator Ruby extensions."""

    REPO_DIR = "/workspace/github-changelog-generator"

    def _read(self, *parts):
        fpath = os.path.join(self.REPO_DIR, *parts)
        assert os.path.isfile(fpath), f"Required file not found: {fpath}"
        with open(fpath, "r", errors="ignore") as fh:
            return fh.read()

    # ------------------------------------------------------------------
    # L1: File existence
    # ------------------------------------------------------------------

    def test_section_config_exists(self):
        """section_config.rb must exist."""
        assert os.path.isfile(
            os.path.join(
                self.REPO_DIR, "lib", "github_changelog_generator", "section_config.rb"
            )
        )

    def test_keep_a_changelog_formatter_exists(self):
        """formatter/keep_a_changelog.rb must exist."""
        base = os.path.join(
            self.REPO_DIR, "lib", "github_changelog_generator", "formatter"
        )
        candidates = [
            os.path.join(base, "keep_a_changelog.rb"),
            os.path.join(base, "keepachangelog.rb"),
            os.path.join(base, "keep_changelog.rb"),
        ]
        assert any(
            os.path.isfile(c) for c in candidates
        ), "Keep-a-Changelog formatter not found"

    def test_config_file_exists(self):
        """.github_changelog_generator config file must exist."""
        assert os.path.isfile(
            os.path.join(self.REPO_DIR, ".github_changelog_generator")
        )

    # ------------------------------------------------------------------
    # L1: Ruby syntax check
    # ------------------------------------------------------------------

    def test_section_config_valid_ruby(self):
        """section_config.rb must be syntactically valid Ruby."""
        result = subprocess.run(
            ["ruby", "-c", "lib/github_changelog_generator/section_config.rb"],
            cwd=self.REPO_DIR,
            capture_output=True,
            text=True,
            timeout=30,
        )
        assert result.returncode == 0, f"Ruby syntax error:\n{result.stderr}"

    def test_formatter_valid_ruby(self):
        """keep_a_changelog.rb must be syntactically valid Ruby."""
        base = os.path.join(
            self.REPO_DIR, "lib", "github_changelog_generator", "formatter"
        )
        for name in ("keep_a_changelog.rb", "keepachangelog.rb", "keep_changelog.rb"):
            fpath = os.path.join(base, name)
            if os.path.isfile(fpath):
                result = subprocess.run(
                    ["ruby", "-c", fpath],
                    cwd=self.REPO_DIR,
                    capture_output=True,
                    text=True,
                    timeout=30,
                )
                assert (
                    result.returncode == 0
                ), f"Ruby syntax error in {name}:\n{result.stderr}"
                return
        pytest.fail("No formatter Ruby file found to check")

    # ------------------------------------------------------------------
    # L2: Label-to-section mapping
    # ------------------------------------------------------------------

    def test_label_mapping_defined(self):
        """section_config.rb must define label-to-section mapping."""
        content = self._read("lib", "github_changelog_generator", "section_config.rb")
        # Expect hash/map with label keys
        patterns = [
            r"(enhancement|bug|feature|breaking|deprecat)",
            r"(LABEL|label|section)",
        ]
        assert any(
            re.search(p, content, re.IGNORECASE) for p in patterns
        ), "No label-to-section mapping found"

    def test_mapping_has_multiple_labels(self):
        """Mapping should cover at least 3 distinct label categories."""
        content = self._read("lib", "github_changelog_generator", "section_config.rb")
        categories = 0
        for kw in (
            "enhancement",
            "bug",
            "feature",
            "breaking",
            "deprecat",
            "security",
            "removed",
            "fix",
        ):
            if re.search(kw, content, re.IGNORECASE):
                categories += 1
        assert categories >= 3, f"Only {categories} label categories found (need >= 3)"

    def test_section_config_has_class_or_module(self):
        """section_config.rb should define a class or module."""
        content = self._read("lib", "github_changelog_generator", "section_config.rb")
        assert re.search(
            r"(class|module)\s+\w+", content
        ), "section_config.rb should define a class or module"

    # ------------------------------------------------------------------
    # L2: Keep a Changelog formatter
    # ------------------------------------------------------------------

    def test_formatter_produces_sections(self):
        """Formatter should produce section headers (Added, Changed, etc.)."""
        base = os.path.join(
            self.REPO_DIR, "lib", "github_changelog_generator", "formatter"
        )
        content = ""
        for name in ("keep_a_changelog.rb", "keepachangelog.rb", "keep_changelog.rb"):
            fpath = os.path.join(base, name)
            if os.path.isfile(fpath):
                with open(fpath, "r", errors="ignore") as fh:
                    content = fh.read()
                break
        kac_sections = [
            "Added",
            "Changed",
            "Deprecated",
            "Removed",
            "Fixed",
            "Security",
        ]
        found = sum(1 for s in kac_sections if re.search(s, content, re.IGNORECASE))
        assert found >= 3, f"Formatter references only {found} KAC sections (need >= 3)"

    def test_formatter_has_render_method(self):
        """Formatter should define a render/format/generate method."""
        base = os.path.join(
            self.REPO_DIR, "lib", "github_changelog_generator", "formatter"
        )
        content = ""
        for name in ("keep_a_changelog.rb", "keepachangelog.rb", "keep_changelog.rb"):
            fpath = os.path.join(base, name)
            if os.path.isfile(fpath):
                with open(fpath, "r", errors="ignore") as fh:
                    content = fh.read()
                break
        assert re.search(
            r"def\s+(render|format|generate|to_s|call)", content
        ), "Formatter missing render/format/generate method"

    # ------------------------------------------------------------------
    # L2: Config file
    # ------------------------------------------------------------------

    def test_config_file_not_empty(self):
        """Config file should have content."""
        content = self._read(".github_changelog_generator")
        assert (
            len(content.strip()) > 10
        ), ".github_changelog_generator is effectively empty"

    def test_config_has_key_value_pairs(self):
        """Config should contain key=value style settings."""
        content = self._read(".github_changelog_generator")
        assert re.search(
            r"^\w[\w-]+=.+$", content, re.MULTILINE
        ), "Config file missing key=value pairs"

    def test_config_references_labels(self):
        """Config should reference label configuration."""
        content = self._read(".github_changelog_generator")
        patterns = [
            r"enhancement.?label",
            r"bug.?label",
            r"add.?label",
            r"label",
        ]
        assert any(
            re.search(p, content, re.IGNORECASE) for p in patterns
        ), "Config file does not reference label settings"
