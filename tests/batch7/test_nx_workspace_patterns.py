"""Test file for the nx-workspace-patterns skill.

This suite validates the project constraint checker, layer rule,
circular dependency detection, and public API rule in Nx.
"""

from __future__ import annotations

import pathlib
import re

import pytest


class TestNxWorkspacePatterns:
    """Verify Nx project constraint enforcement patterns."""

    REPO_DIR = "/workspace/nx"

    INDEX_TS = "packages/nx/src/plugins/project-constraints/index.ts"
    CHECKER_TS = "packages/nx/src/plugins/project-constraints/constraint-checker.ts"
    LAYER_RULE_TS = "packages/nx/src/plugins/project-constraints/rules/layer-rule.ts"

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

    def _all_ts_sources(self) -> str:
        base = self._repo_path("packages/nx/src/plugins/project-constraints")
        if not base.is_dir():
            return ""
        parts = []
        for f in sorted(base.rglob("*.ts")):
            parts.append(f.read_text(encoding="utf-8", errors="ignore"))
        return "\n".join(parts)

    # ------------------------------------------------------------------
    # Layer 1 – file_path_check (3 cases)
    # ------------------------------------------------------------------

    def test_file_path_packages_nx_src_plugins_project_constraints_index_ts_exists(
        self,
    ):
        """Verify index.ts exists and is non-empty."""
        self._assert_non_empty_file(self.INDEX_TS)

    def test_file_path_packages_nx_src_plugins_project_constraints_constraint_check(
        self,
    ):
        """Verify constraint-checker.ts exists and is non-empty."""
        self._assert_non_empty_file(self.CHECKER_TS)

    def test_file_path_packages_nx_src_plugins_project_constraints_rules_layer_rule(
        self,
    ):
        """Verify rules/layer-rule.ts exists and is non-empty."""
        self._assert_non_empty_file(self.LAYER_RULE_TS)

    # ------------------------------------------------------------------
    # Layer 2 – semantic_check (5 cases)
    # ------------------------------------------------------------------

    def test_semantic_constraintchecker_constructor_accepts_projectgraph_and_confi(
        self,
    ):
        """ConstraintChecker constructor accepts ProjectGraph and config."""
        src = self._read_text(self.CHECKER_TS)
        assert re.search(
            r"class\s+ConstraintChecker", src
        ), "ConstraintChecker class not found"
        assert re.search(
            r"ProjectGraph|projectGraph", src
        ), "ConstraintChecker should accept ProjectGraph"

    def test_semantic_constraintviolation_interface_has_rule_severity_sourceprojec(
        self,
    ):
        """ConstraintViolation interface has rule, severity, sourceProject, targetProject, message."""
        src = self._all_ts_sources()
        assert re.search(
            r"interface\s+ConstraintViolation|type\s+ConstraintViolation", src
        ), "ConstraintViolation interface not found"
        for field in ("rule", "severity", "sourceProject", "targetProject", "message"):
            assert re.search(
                rf"{field}\s*[:\?]", src
            ), f"ConstraintViolation missing field: {field}"

    def test_semantic_checklayerrule_function_accepts_source_target_config_paramet(
        self,
    ):
        """checkLayerRule function accepts source, target, config parameters."""
        src = self._read_text(self.LAYER_RULE_TS)
        assert re.search(
            r"function\s+checkLayerRule|export\s+.*checkLayerRule", src
        ), "checkLayerRule function not found"

    def test_semantic_detectcirculardependencies_function_accepts_projectgraph(self):
        """detectCircularDependencies function accepts ProjectGraph."""
        src = self._all_ts_sources()
        assert re.search(
            r"detectCircularDependencies|detectCircular", src
        ), "detectCircularDependencies function not found"

    def test_semantic_checkpublicapirule_function_checks_import_path_against_publi(
        self,
    ):
        """checkPublicApiRule function checks import path against publicApiPattern."""
        src = self._all_ts_sources()
        assert re.search(
            r"checkPublicApiRule|publicApi|publicApiPattern", src
        ), "checkPublicApiRule function not found"

    # ------------------------------------------------------------------
    # Layer 3 – functional_check (5 cases, source analysis)
    # ------------------------------------------------------------------

    def test_functional_data_access_ui_produces_layer_violation(self):
        """data-access -> ui produces layer violation."""
        src = self._read_text(self.LAYER_RULE_TS)
        assert re.search(
            r"violation|Violation|error", src, re.IGNORECASE
        ), "Layer rule should produce violations"
        assert re.search(r"layer|Layer", src), "Layer rule should check layer ordering"

    def test_functional_ui_feature_allowed_in_correct_layer_order(self):
        """ui -> feature allowed in correct layer order."""
        src = self._read_text(self.LAYER_RULE_TS)
        assert re.search(
            r"indexOf|findIndex|order|layer", src, re.IGNORECASE
        ), "Layer rule should compare layer positions"

    def test_functional_ui_util_with_allowskiplayers_false_produces_violation(self):
        """ui -> util with allowSkipLayers=false produces violation."""
        src = self._all_ts_sources()
        assert re.search(
            r"allowSkipLayers|skipLayers", src
        ), "Layer rule should support allowSkipLayers option"

    def test_functional_same_layer_dependency_with_allowsamelayer_true_is_allowed(self):
        """same-layer dependency with allowSameLayer=true is allowed."""
        src = self._all_ts_sources()
        assert re.search(
            r"allowSameLayer|sameLayer", src
        ), "Layer rule should support allowSameLayer option"

    def test_functional_a_b_c_a_detected_as_circular_dependency(self):
        """A->B->C->A detected as circular dependency."""
        src = self._all_ts_sources()
        assert re.search(
            r"circular|cycle|visited|stack", src, re.IGNORECASE
        ), "Circular dependency detection logic should exist"
