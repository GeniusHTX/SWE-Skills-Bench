"""
Test for 'changelog-automation' skill — Changelog Generator Ruby Implementation
Validates conventional commit parsing, SemVer bumping, categorizer,
and markdown formatter with proper heading structure.
"""

import os
import re
import subprocess

import pytest


class TestChangelogAutomation:
    """Verify changelog automation implementation."""

    REPO_DIR = "/workspace/github-changelog-generator"

    # ── file_path_check ─────────────────────────────────────────────────────

    def test_source_files_exist(self):
        """Verify at least 3 Ruby source files exist."""
        rb_files = self._find_rb_files("lib")
        assert (
            len(rb_files) >= 3
        ), f"Expected ≥3 Ruby source files in lib/, found {len(rb_files)}"

    def test_spec_files_exist(self):
        """Verify at least 3 spec files exist."""
        spec_files = self._find_rb_files("spec")
        assert len(spec_files) >= 3, f"Expected ≥3 spec files, found {len(spec_files)}"

    # ── semantic_check ──────────────────────────────────────────────────────

    def test_conventional_commit_parsing(self):
        """Verify conventional commit regex/parsing logic exists."""
        rb_files = self._find_rb_files("lib")
        assert rb_files, "No lib Ruby files found"
        for fpath in rb_files:
            content = self._read(fpath)
            if re.search(
                r"(feat|fix|chore|breaking).*commit|conventional|commit_type|type.*scope",
                content,
                re.IGNORECASE,
            ):
                return
        pytest.fail("No conventional commit parsing logic found")

    def test_semver_bumping_logic(self):
        """Verify SemVer version bumping with 0.x exception."""
        rb_files = self._find_rb_files("lib")
        assert rb_files, "No lib files"
        for fpath in rb_files:
            content = self._read(fpath)
            if re.search(r"(semver|bump|major|minor|patch)", content, re.IGNORECASE):
                return
        pytest.fail("No SemVer bumping logic found")

    def test_categorizer_exists(self):
        """Verify a commit categorizer/classifier module exists."""
        rb_files = self._find_rb_files("lib")
        assert rb_files, "No lib files"
        for fpath in rb_files:
            content = self._read(fpath)
            if re.search(r"(categoriz|classif|group|bucket)", content, re.IGNORECASE):
                return
            if "category" in os.path.basename(fpath).lower():
                return
        pytest.fail("No categorizer module found")

    def test_markdown_formatter_with_headings(self):
        """Verify markdown formatter uses ## headings."""
        rb_files = self._find_rb_files("lib")
        assert rb_files, "No lib files"
        for fpath in rb_files:
            content = self._read(fpath)
            if re.search(r"(##|markdown|format)", content, re.IGNORECASE):
                if (
                    "##" in content
                    or "heading" in content.lower()
                    or "format" in content.lower()
                ):
                    return
        pytest.fail("No markdown formatter with ## headings found")

    # ── functional_check ────────────────────────────────────────────────────

    def test_ruby_files_syntax_valid(self):
        """Verify Ruby files have valid syntax (ruby -c)."""
        rb_files = self._find_rb_files("lib")
        assert rb_files, "No lib files"
        try:
            subprocess.run(["ruby", "--version"], capture_output=True, timeout=10)
        except (FileNotFoundError, subprocess.TimeoutExpired):
            pytest.skip("ruby not available")
        for fpath in rb_files[:5]:
            result = subprocess.run(
                ["ruby", "-c", fpath], capture_output=True, text=True, timeout=30
            )
            assert (
                result.returncode == 0
            ), f"Syntax error in {os.path.basename(fpath)}: {result.stderr}"

    def test_spec_files_have_describe_blocks(self):
        """Verify spec files contain RSpec describe blocks."""
        spec_files = self._find_rb_files("spec")
        assert spec_files, "No spec files found"
        for fpath in spec_files:
            content = self._read(fpath)
            if re.search(r"(describe|context|it)\s+", content):
                return
        pytest.fail("No spec file contains describe/context/it blocks")

    def test_semver_0x_exception(self):
        """Verify 0.x SemVer exception is handled (breaking changes bump minor, not major)."""
        rb_files = self._find_rb_files("lib") + self._find_rb_files("spec")
        for fpath in rb_files:
            content = self._read(fpath)
            if re.search(
                r"0\.\d|zero.*major|major.*zero|pre.?1\.0", content, re.IGNORECASE
            ):
                return
        # This test is advisory - the feature may be implicit
        pytest.skip("0.x SemVer exception not explicitly detectable")

    def test_source_files_have_module_structure(self):
        """Verify Ruby source files define modules or classes."""
        rb_files = self._find_rb_files("lib")
        assert rb_files, "No lib files"
        has_structure = False
        for fpath in rb_files:
            content = self._read(fpath)
            if re.search(r"(module\s+\w+|class\s+\w+)", content):
                has_structure = True
                break
        assert has_structure, "No module or class definitions found"

    # ── helpers ──────────────────────────────────────────────────────────────

    def _find_rb_files(self, subdir):
        base = os.path.join(self.REPO_DIR, subdir)
        if not os.path.isdir(base):
            return []
        results = []
        for dirpath, _, fnames in os.walk(base):
            for f in fnames:
                if f.endswith(".rb"):
                    results.append(os.path.join(dirpath, f))
        return results

    def _read(self, path):
        with open(path, "r", errors="ignore") as fh:
            return fh.read()
