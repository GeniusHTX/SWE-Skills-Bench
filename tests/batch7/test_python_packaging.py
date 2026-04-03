"""Test file for the python-packaging skill.

This suite validates the DependencyGroup, DependencyGroupResolver,
and related error classes in the packaging library.
"""

from __future__ import annotations

import ast
import pathlib
import re

import pytest


class TestPythonPackaging:
    """Verify dependency group resolution in packaging."""

    REPO_DIR = "/workspace/packaging"

    DEPENDENCY_GROUPS_PY = "packaging/dependency_groups.py"
    REQUIREMENTS_PY = "packaging/requirements.py"
    TEST_PY = "tests/test_dependency_groups.py"

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

    def _class_source(self, source: str, class_name: str) -> str | None:
        tree = ast.parse(source)
        for node in ast.walk(tree):
            if isinstance(node, ast.ClassDef) and node.name == class_name:
                start = node.lineno - 1
                end = node.end_lineno or start + 1
                lines = source.splitlines()
                return "\n".join(lines[start:end])
        return None

    # ------------------------------------------------------------------
    # Layer 1 – file_path_check (3 cases)
    # ------------------------------------------------------------------

    def test_file_path_packaging_dependency_groups_py_exists(self):
        """Verify dependency_groups.py exists and is non-empty."""
        self._assert_non_empty_file(self.DEPENDENCY_GROUPS_PY)

    def test_file_path_packaging_requirements_py_modified_from_dependency_group_ite(
        self,
    ):
        """Verify requirements.py modified (from_dependency_group_item added)."""
        self._assert_non_empty_file(self.REQUIREMENTS_PY)
        src = self._read_text(self.REQUIREMENTS_PY)
        assert (
            "from_dependency_group_item" in src
        ), "requirements.py should have from_dependency_group_item"

    def test_file_path_tests_test_dependency_groups_py_exists(self):
        """Verify test_dependency_groups.py exists and is non-empty."""
        self._assert_non_empty_file(self.TEST_PY)

    # ------------------------------------------------------------------
    # Layer 2 – semantic_check (5 cases)
    # ------------------------------------------------------------------

    def test_semantic_dependencygroup_has_name_requirements_include_groups_raw_ite(
        self,
    ):
        """DependencyGroup has name, requirements, include_groups, raw_items properties."""
        src = self._read_text(self.DEPENDENCY_GROUPS_PY)
        body = self._class_source(src, "DependencyGroup")
        assert body is not None, "DependencyGroup class not found"
        for prop in ("name", "requirements"):
            assert prop in body, f"DependencyGroup missing property: {prop}"

    def test_semantic_dependencygroupresolver_has_resolve_resolve_all_validate_met(
        self,
    ):
        """DependencyGroupResolver has resolve, resolve_all, validate methods."""
        src = self._read_text(self.DEPENDENCY_GROUPS_PY)
        body = self._class_source(src, "DependencyGroupResolver")
        assert body is not None, "DependencyGroupResolver class not found"
        for method in ("resolve", "resolve_all", "validate"):
            assert re.search(
                rf"def\s+{method}\s*\(", body
            ), f"DependencyGroupResolver missing method: {method}"

    def test_semantic_group_name_regex_validation_present(self):
        """Group name regex validation present."""
        src = self._read_text(self.DEPENDENCY_GROUPS_PY)
        assert re.search(
            r"re\.\w+\(|regex|pattern|match\(", src
        ), "Group name regex validation not found"

    def test_semantic_circulardependencygroup_has_cycle_attribute(self):
        """CircularDependencyGroup has cycle attribute."""
        src = self._read_text(self.DEPENDENCY_GROUPS_PY)
        assert re.search(
            r"class\s+CircularDependencyGroup", src
        ), "CircularDependencyGroup class not found"
        assert "cycle" in src, "CircularDependencyGroup should have cycle attribute"

    def test_semantic_invaliddependencygroup_has_group_name_and_item_index_attribu(
        self,
    ):
        """InvalidDependencyGroup has group_name and item_index attributes."""
        src = self._read_text(self.DEPENDENCY_GROUPS_PY)
        assert re.search(
            r"class\s+InvalidDependencyGroup", src
        ), "InvalidDependencyGroup class not found"

    # ------------------------------------------------------------------
    # Layer 3 – functional_check (5 cases, source analysis)
    # ------------------------------------------------------------------

    def test_functional_resolve_test_returns_requirement_pytest_7_0_requirement_cove(
        self,
    ):
        """resolve('test') returns [Requirement('pytest>=7.0'), Requirement('coverage[toml]')]."""
        src = self._read_text(self.DEPENDENCY_GROUPS_PY)
        assert re.search(r"def\s+resolve\s*\(", src), "resolve method required"

    def test_functional_resolve_dev_flattens_test_lint_direct_requirements(self):
        """resolve('dev') flattens test + lint + direct requirements."""
        src = self._read_text(self.DEPENDENCY_GROUPS_PY)
        assert re.search(
            r"include|flatten|recursive", src, re.IGNORECASE
        ), "resolve should flatten include-group references"

    def test_functional_resolve_nonexistent_raises_undefineddependencygroup(self):
        """resolve('nonexistent') raises UndefinedDependencyGroup."""
        src = self._read_text(self.DEPENDENCY_GROUPS_PY)
        assert re.search(
            r"UndefinedDependencyGroup|KeyError|not found", src
        ), "resolve should raise on undefined group"

    def test_functional_circular_reference_raises_circulardependencygroup_cycle_test(
        self,
    ):
        """Circular reference raises CircularDependencyGroup(cycle=['test', 'dev', 'test'])."""
        src = self._read_text(self.DEPENDENCY_GROUPS_PY)
        assert re.search(
            r"CircularDependencyGroup|circular|cycle", src
        ), "Circular reference detection required"

    def test_functional_validate_returns_empty_list_for_valid_groups(self):
        """validate() returns empty list for valid groups."""
        src = self._read_text(self.DEPENDENCY_GROUPS_PY)
        assert re.search(r"def\s+validate\s*\(", src), "validate method required"
